from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "benchmarks" / "results" / "prompt-ab-baseline.json"
V2_PATH = ROOT / "benchmarks" / "publication" / "prompt-ab-baseline-v2.json"
SCHEMA_PATH = ROOT / ".portfolio" / "contracts" / "benchmark-result-v2.schema.json"
CONFIG_PATH = ROOT / "benchmarks" / "config" / "prompt-ab-baseline-v2.json"
FIXTURE_PATH = ROOT / "data" / "fixtures"
OUTPUTS_PATH = FIXTURE_PATH / "outputs.jsonl"
PROVENANCE_PATH = FIXTURE_PATH / "outputs.provenance.json"
GENERATION_CASES_PATH = FIXTURE_PATH / "generation-cases.jsonl"
TEMPLATES_PATH = FIXTURE_PATH / "prompt-templates.json"
LOCK_PATH = ROOT / "requirements-validation.lock"
PRODUCER_PATH = ROOT / "tools" / "generate-publication-benchmark.py"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load_producer() -> Any:
    spec = importlib.util.spec_from_file_location("publication_benchmark", PRODUCER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load publication producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_has_commit(commit: str) -> bool:
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={ROOT}",
            "-C",
            str(ROOT),
            "cat-file",
            "-e",
            f"{commit}^{{commit}}",
        ],
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-git", action="store_true")
    args = parser.parse_args()

    manifest = (ROOT / "project.yaml").read_text(encoding="utf-8")
    published = re.search(r"(?m)^status:\s*published\s*$", manifest) is not None
    lock = LOCK_PATH.read_text(encoding="utf-8")
    require("jsonschema==4.26.0" in lock, "jsonschema is not pinned")
    require("setuptools==80.9.0" in lock, "setuptools is not pinned")

    config = read_json(CONFIG_PATH)
    require(config["measured_cases"] == 10, "publication config case count mismatch")
    require(config["variant_count"] == 3, "publication config variant count mismatch")
    require(config["measured_outputs"] == 30, "publication config output count mismatch")
    require(config["concurrency"] == 1, "publication config concurrency mismatch")
    if not V2_PATH.is_file():
        require(not published, "published project requires V2 evidence")
        print("publication_evidence=not-applicable")
        return

    import jsonschema

    v1 = read_json(V1_PATH)
    v2 = read_json(V2_PATH)
    schema = read_json(SCHEMA_PATH)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(v2)

    require(v1.get("project") == "prompt-ab-testing", "unexpected V1 project")
    require(v2.get("project") == "prompt-ab-testing", "unexpected V2 project")
    require(
        v2.get("benchmark_id") == "local-llm-blinded-prompt-ab-v2",
        "unexpected benchmark id",
    )
    require(v1.get("metric") == "highest_mean_score", "unexpected primary metric")
    require(v1.get("value") == 0.8, "unexpected highest mean baseline")
    require(v1.get("repeat") == 1, "workload size must not be reported as run repetition")
    require(v1.get("measured_iterations") == 30, "top-level output count mismatch")

    summary = v1.get("summary", {})
    require(summary.get("case_count") == 10, "expected ten cases")
    require(summary.get("variant_count") == 3, "expected three variants")
    require(summary.get("measured_iterations") == 30, "measured output count mismatch")
    require(summary.get("leader_count") == 2, "expected two tied leaders")
    require(
        summary.get("apparent_leader_conclusive") is False,
        "tied-leader conclusion must remain inconclusive",
    )
    require(v1.get("leading_variant_ids") == ["v_02", "v_03"], "unexpected leaders")

    variants = {row["variant_id"]: row for row in v1.get("variants", [])}
    require(variants.get("v_01", {}).get("mean_score") == 0.0, "baseline mean mismatch")
    leader = variants.get("v_02", {})
    require(leader.get("mean_score") == 0.8, "leader mean mismatch")
    require(leader.get("ci95_lower") == 0.5, "leader interval lower bound mismatch")
    require(leader.get("ci95_upper") == 1.0, "leader interval upper bound mismatch")
    require(leader.get("ci95_method") == "seeded-bootstrap", "interval method mismatch")
    require(leader.get("bootstrap_resamples") == 10_000, "bootstrap count mismatch")

    comparison = v1.get("paired_comparison", {})
    require(comparison.get("ci95_method") == "tie", "leaders must remain tied")
    require(comparison.get("conclusive") is False, "tie must remain inconclusive")
    baseline_comparisons = v1.get("baseline_comparisons", [])
    require(len(baseline_comparisons) == 2, "expected two baseline comparisons")
    for row in baseline_comparisons:
        require(row.get("baseline_variant_id") == "v_01", "baseline ID mismatch")
        require(row.get("mean_uplift") == 0.8, "paired uplift mismatch")
        require(row.get("uplift_ci95_lower") == 0.5, "uplift lower mismatch")
        require(row.get("uplift_ci95_upper") == 1.0, "uplift upper mismatch")
        require(row.get("conclusive") is True, "baseline uplift must be conclusive")

    metric = v2["metrics"][0]
    require(metric["name"] == "highest_mean_score", "unexpected V2 metric")
    require(metric["value"] == v1["value"], "V1/V2 value mismatch")
    require(metric["samples"] == v1["samples"], "V1/V2 samples mismatch")
    require(metric["failures"] == 0, "publication contains failures")
    require(v2["execution"]["repeat"] == 1, "execution repeat mismatch")
    require(v2["workload"]["measured_iterations"] == 30, "workload output count mismatch")
    require(v2["workload"]["warmup_iterations"] == 0, "unexpected warmup")
    require(v2["workload"]["concurrency"] == 1, "unexpected concurrency")
    require(
        v2["provenance"]["artifact_digest"] == sha256_file(V1_PATH),
        "raw artifact digest mismatch",
    )
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", v2["provenance"]["image_digest"])
        is not None,
        "invalid image digest",
    )
    require(v2["comparability_key"] == config["comparability_key"], "comparability key mismatch")

    provenance = read_json(PROVENANCE_PATH)
    provider = provenance.get("provider", {})
    generation = provenance.get("generation", {})
    producer = provenance.get("producer", {})
    artifacts = provenance.get("artifacts", {})
    require(provider.get("model") == config["model"], "generation model mismatch")
    require(provider.get("model_digest") == config["model_digest"], "model digest mismatch")
    require(generation.get("measured_requests") == 30, "generation request count mismatch")
    require(generation.get("failures") == 0, "generation contains failures")
    require(generation.get("warmup_iterations") == 1, "generation warmup mismatch")
    require(generation.get("prompt_tokens") == 2158, "prompt token count mismatch")
    require(generation.get("completion_tokens") == 262, "completion token count mismatch")
    require(artifacts.get("outputs_sha256") == sha256_file(OUTPUTS_PATH), "output digest mismatch")
    require(artifacts.get("generation_cases_sha256") == sha256_file(GENERATION_CASES_PATH), "generation case digest mismatch")
    require(artifacts.get("templates_sha256") == sha256_file(TEMPLATES_PATH), "template digest mismatch")
    require(re.fullmatch(r"[0-9a-f]{40}", producer.get("source_commit", "")) is not None, "invalid producer source")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", producer.get("image_digest", "")) is not None, "invalid producer image")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in ("0.80", "+0.80", "0.50", "30", "941.55"):
        require(expected in readme, f"README is missing benchmark value {expected}")
    require(
        "result_path: benchmarks/publication/prompt-ab-baseline-v2.json" in manifest,
        "manifest V2 path mismatch",
    )

    if args.require_git:
        source_commit = v2["provenance"]["source_commit"]
        require(git_has_commit(source_commit), "source commit unavailable; fetch full history")
        require(git_has_commit(producer["source_commit"]), "producer source commit unavailable")
        producer = load_producer()
        require(
            v2["workload"]["fixture_digest"]
            == producer.digest_committed_path(ROOT, FIXTURE_PATH, source_commit),
            "committed fixture digest mismatch",
        )
        require(
            v2["workload"]["config_digest"]
            == producer.digest_committed_path(ROOT, CONFIG_PATH, source_commit),
            "committed config digest mismatch",
        )
        require(
            v2["provenance"]["dependency_lock_digest"]
            == producer.digest_committed_path(ROOT, LOCK_PATH, source_commit),
            "committed validation-lock digest mismatch",
        )

    serialized = json.dumps({"v1": v1, "v2": v2})
    for forbidden in ("C:\\Users\\", "github" + "_pat_", "gh" + "p_"):
        require(forbidden not in serialized, f"forbidden value in evidence: {forbidden}")
    print("publication_evidence=passed")


if __name__ == "__main__":
    main()
