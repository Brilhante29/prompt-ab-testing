import argparse
import json
import math
import os
import platform
import random
import re
import sys
from itertools import product
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .producer import (
    GenerationValidationError,
    OpenAICompatibleGenerator,
    generate_output_matrix,
)


DEFAULT_CASES = "data/fixtures/cases.jsonl"
DEFAULT_OUTPUTS = "data/fixtures/outputs.jsonl"
DEFAULT_VARIANTS = "data/fixtures/variants.json"
DEFAULT_OUTPUT = "benchmarks/results/prompt-ab-baseline.json"
DEFAULT_GENERATION_CASES = "data/fixtures/generation-cases.jsonl"
DEFAULT_TEMPLATES = "data/fixtures/prompt-templates.json"
DEFAULT_PROVENANCE = "data/fixtures/outputs.provenance.json"
COMMAND = (
    "python -m prompt_ab_testing benchmark --cases data/fixtures/cases.jsonl "
    "--outputs data/fixtures/outputs.jsonl --variants data/fixtures/variants.json "
    "--output benchmarks/results/prompt-ab-baseline.json"
)
SUPPORTED_METRICS = {"exact_match", "token_f1"}


class ExperimentValidationError(ValueError):
    """Raised when an experiment is malformed, incomplete, or unblinded."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExperimentValidationError(
                f"{path}:{line_number}: invalid JSON"
            ) from exc
        if not isinstance(value, dict):
            raise ExperimentValidationError(f"{path}:{line_number}: expected an object")
        records.append(value)
    if not records:
        raise ExperimentValidationError(f"{path}: expected at least one record")
    return records


def _require_exact_keys(record: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - record.keys()
    extra = record.keys() - required
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {sorted(missing)}")
        if extra:
            details.append(f"unexpected {sorted(extra)}")
        raise ExperimentValidationError(f"{label}: {', '.join(details)}")


def load_variants(path: str | Path) -> list[str]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExperimentValidationError(f"{path}: invalid JSON") from exc
    if not isinstance(document, dict):
        raise ExperimentValidationError(f"{path}: expected an object")
    _require_exact_keys(document, {"blinded", "variant_ids"}, "variants")
    if document["blinded"] is not True:
        raise ExperimentValidationError("variants.blinded: must be true")
    variant_ids = document["variant_ids"]
    if not isinstance(variant_ids, list) or len(variant_ids) < 2:
        raise ExperimentValidationError(
            "variants.variant_ids: expected at least two IDs"
        )
    if not all(
        isinstance(variant_id, str)
        and re.fullmatch(r"v_[0-9]{2,}", variant_id)
        for variant_id in variant_ids
    ):
        raise ExperimentValidationError(
            "variants.variant_ids: use opaque IDs such as v_01"
        )
    if len(set(variant_ids)) != len(variant_ids):
        raise ExperimentValidationError("variants.variant_ids: IDs must be unique")
    return variant_ids


def validate_cases(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    for index, case in enumerate(records, start=1):
        label = f"case[{index}]"
        _require_exact_keys(case, {"id", "metric", "expected"}, label)
        if (
            not isinstance(case["id"], str)
            or not case["id"].strip()
            or case["id"] in seen
        ):
            raise ExperimentValidationError(
                f"{label}.id: expected a unique non-empty string"
            )
        if case["metric"] not in SUPPORTED_METRICS:
            raise ExperimentValidationError(
                f"{label}.metric: expected one of {sorted(SUPPORTED_METRICS)}"
            )
        if not isinstance(case["expected"], str) or not case["expected"].strip():
            raise ExperimentValidationError(
                f"{label}.expected: expected a non-empty string"
            )
        seen.add(case["id"])
    return records


def validate_outputs(
    records: list[dict[str, Any]], case_ids: set[str], variant_ids: set[str]
) -> dict[tuple[str, str], str]:
    matrix: dict[tuple[str, str], str] = {}
    for index, output in enumerate(records, start=1):
        label = f"output[{index}]"
        _require_exact_keys(output, {"case_id", "variant_id", "output"}, label)
        case_id = output["case_id"]
        variant_id = output["variant_id"]
        if case_id not in case_ids:
            raise ExperimentValidationError(f"{label}.case_id: unknown case")
        if variant_id not in variant_ids:
            raise ExperimentValidationError(f"{label}.variant_id: unknown variant")
        if not isinstance(output["output"], str):
            raise ExperimentValidationError(f"{label}.output: expected a string")
        key = (case_id, variant_id)
        if key in matrix:
            raise ExperimentValidationError(
                f"{label}: duplicate output for {case_id}/{variant_id}"
            )
        matrix[key] = output["output"]

    expected_matrix = {
        (case_id, variant_id)
        for case_id in case_ids
        for variant_id in variant_ids
    }
    missing = sorted(expected_matrix - matrix.keys())
    if missing:
        raise ExperimentValidationError(
            f"outputs: incomplete case/variant matrix; missing={missing}"
        )
    return matrix


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def exact_match(expected: str, observed: str) -> float:
    return 1.0 if _tokens(expected) == _tokens(observed) else 0.0


def token_f1(expected: str, observed: str) -> float:
    expected_tokens = Counter(_tokens(expected))
    observed_tokens = Counter(_tokens(observed))
    if not expected_tokens and not observed_tokens:
        return 1.0
    if not expected_tokens or not observed_tokens:
        return 0.0
    overlap = sum((expected_tokens & observed_tokens).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(observed_tokens.values())
    recall = overlap / sum(expected_tokens.values())
    return 2 * precision * recall / (precision + recall)


def score_case(metric: str, expected: str, observed: str) -> float:
    if metric == "exact_match":
        return exact_match(expected, observed)
    if metric == "token_f1":
        return token_f1(expected, observed)
    raise ExperimentValidationError(f"unsupported metric: {metric}")


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return (
        ordered[lower_index] * (1 - fraction)
        + ordered[upper_index] * fraction
    )


def bootstrap_mean_ci95(
    values: list[float],
    *,
    max_resamples: int = 10_000,
    seed: int = 20_260_803,
) -> tuple[float, float, float, int, str]:
    if not values:
        raise ExperimentValidationError("bootstrap requires at least one value")
    sample_count = len(values)
    exact_resamples = sample_count**sample_count
    if exact_resamples <= max_resamples:
        index_sets = product(range(sample_count), repeat=sample_count)
        method = "exhaustive-bootstrap"
        resample_count = exact_resamples
    else:
        generator = random.Random(seed)
        index_sets = (
            tuple(generator.randrange(sample_count) for _ in range(sample_count))
            for _ in range(max_resamples)
        )
        method = "seeded-bootstrap"
        resample_count = max_resamples

    means = [
        sum(values[index] for index in indices) / sample_count
        for indices in index_sets
    ]
    mean = sum(values) / sample_count
    return (
        mean,
        _percentile(means, 0.025),
        _percentile(means, 0.975),
        resample_count,
        method,
    )


def evaluate(
    cases_path: str | Path = DEFAULT_CASES,
    outputs_path: str | Path = DEFAULT_OUTPUTS,
    variants_path: str | Path = DEFAULT_VARIANTS,
) -> dict[str, Any]:
    variant_ids = load_variants(variants_path)
    cases = validate_cases(load_jsonl(cases_path))
    matrix = validate_outputs(
        load_jsonl(outputs_path),
        {case["id"] for case in cases},
        set(variant_ids),
    )

    variants: list[dict[str, Any]] = []
    scores_by_variant: dict[str, list[float]] = {}
    means_by_variant: dict[str, float] = {}
    for variant_id in variant_ids:
        scores = [
            score_case(
                case["metric"],
                case["expected"],
                matrix[(case["id"], variant_id)],
            )
            for case in cases
        ]
        mean, lower, upper, resample_count, interval_method = bootstrap_mean_ci95(
            scores
        )
        scores_by_variant[variant_id] = scores
        means_by_variant[variant_id] = mean
        variants.append(
            {
                "variant_id": variant_id,
                "mean_score": round(mean, 4),
                "ci95_lower": round(lower, 4),
                "ci95_upper": round(upper, 4),
                "ci95_method": interval_method,
                "bootstrap_resamples": resample_count,
                "sample_count": len(scores),
                "scores": [round(score, 4) for score in scores],
            }
        )

    highest_score_raw = max(means_by_variant.values())
    highest_score = round(highest_score_raw, 4)
    leaders = [
        variant_id
        for variant_id in variant_ids
        if math.isclose(means_by_variant[variant_id], highest_score_raw, abs_tol=1e-12)
    ]
    comparison: dict[str, Any]
    if len(leaders) == 1:
        leader_id = leaders[0]
        runner_up_id = min(
            (variant_id for variant_id in variant_ids if variant_id != leader_id),
            key=lambda variant_id: (-means_by_variant[variant_id], variant_id),
        )
        paired_differences = [
            leader_score - runner_score
            for leader_score, runner_score in zip(
                scores_by_variant[leader_id], scores_by_variant[runner_up_id]
            )
        ]
        uplift, lower, upper, resample_count, interval_method = bootstrap_mean_ci95(
            paired_differences
        )
        comparison = {
            "leader_variant_id": leader_id,
            "runner_up_variant_id": runner_up_id,
            "mean_uplift": round(uplift, 4),
            "uplift_ci95_lower": round(lower, 4),
            "uplift_ci95_upper": round(upper, 4),
            "ci95_method": interval_method,
            "bootstrap_resamples": resample_count,
            "conclusive": lower > 0,
        }
    else:
        comparison = {
            "leader_variant_id": None,
            "runner_up_variant_id": None,
            "mean_uplift": 0.0,
            "uplift_ci95_lower": 0.0,
            "uplift_ci95_upper": 0.0,
            "ci95_method": "tie",
            "bootstrap_resamples": 0,
            "conclusive": False,
        }
    return {
        "project": "prompt-ab-testing",
        "metric": "highest_mean_score",
        "value": highest_score,
        "unit": "ratio",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": COMMAND,
        "repeat": 1,
        "measured_iterations": len(cases) * len(variants),
        "samples": next(
            row["scores"] for row in variants if row["variant_id"] == leaders[0]
        ),
        "summary": {
            "case_count": len(cases),
            "variant_count": len(variants),
            "highest_mean_score": highest_score,
            "leader_count": len(leaders),
            "measured_iterations": len(cases) * len(variants),
            "apparent_leader_conclusive": comparison["conclusive"],
        },
        "environment": {
            "runtime": f"python-{platform.python_version()}",
            "mode": "offline-blinded-output-evaluation",
            "cases_source": str(cases_path),
            "outputs_source": str(outputs_path),
        },
        "blinded": True,
        "leading_variant_ids": leaders,
        "paired_comparison": comparison,
        "variants": variants,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Score supplied blinded prompt outputs; this command does not call an LLM."
    )
    parser.add_argument(
        "command", choices=["benchmark", "generate"], nargs="?", default="benchmark"
    )
    parser.add_argument("--cases", default=DEFAULT_CASES)
    parser.add_argument("--outputs", default=DEFAULT_OUTPUTS)
    parser.add_argument("--variants", default=DEFAULT_VARIANTS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--generation-cases", default=DEFAULT_GENERATION_CASES)
    parser.add_argument("--templates", default=DEFAULT_TEMPLATES)
    parser.add_argument("--provenance", default=DEFAULT_PROVENANCE)
    parser.add_argument("--max-tokens", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            result = generate_output_matrix(
                generator=OpenAICompatibleGenerator.from_environment(),
                cases_path=args.generation_cases,
                templates_path=args.templates,
                variant_ids=load_variants(args.variants),
                output_path=args.outputs,
                provenance_path=args.provenance,
                max_tokens=args.max_tokens,
                warmup_iterations=args.warmup,
                producer_source_commit=os.environ.get(
                    "PROMPT_AB_PRODUCER_SOURCE_COMMIT", "unverified"
                ),
                producer_image_digest=os.environ.get(
                    "PROMPT_AB_PRODUCER_IMAGE_DIGEST", "unverified"
                ),
            )
            print(json.dumps(result, indent=2))
            return
        result = evaluate(args.cases, args.outputs, args.variants)
    except (OSError, ExperimentValidationError, GenerationValidationError) as exc:
        print(f"{args.command} failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
