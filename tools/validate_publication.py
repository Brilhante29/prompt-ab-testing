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
    require(config["measured_cases"] == 4, "publication config case count mismatch")
    require(config["variant_count"] == 3, "publication config variant count mismatch")
    require(config["measured_outputs"] == 12, "publication config output count mismatch")
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
        v2.get("benchmark_id") == "blinded-paired-bootstrap-v1",
        "unexpected benchmark id",
    )
    require(v1.get("metric") == "highest_mean_score", "unexpected primary metric")
    require(v1.get("value") == 0.9365, "unexpected highest mean baseline")
    require(v1.get("repeat") == 1, "workload size must not be reported as run repetition")
    require(v1.get("measured_iterations") == 12, "top-level output count mismatch")

    summary = v1.get("summary", {})
    require(summary.get("case_count") == 4, "expected four cases")
    require(summary.get("variant_count") == 3, "expected three variants")
    require(summary.get("measured_iterations") == 12, "measured output count mismatch")
    require(summary.get("leader_count") == 1, "expected one apparent leader")
    require(
        summary.get("apparent_leader_conclusive") is False,
        "small-fixture conclusion must remain inconclusive",
    )
    require(v1.get("leading_variant_ids") == ["v_01"], "unexpected apparent leader")

    variants = {row["variant_id"]: row for row in v1.get("variants", [])}
    leader = variants.get("v_01", {})
    require(leader.get("mean_score") == 0.9365, "leader mean mismatch")
    require(leader.get("ci95_lower") == 0.873, "leader interval lower bound mismatch")
    require(leader.get("ci95_upper") == 1.0, "leader interval upper bound mismatch")
    require(leader.get("ci95_method") == "exhaustive-bootstrap", "interval method mismatch")
    require(leader.get("bootstrap_resamples") == 256, "bootstrap count mismatch")

    comparison = v1.get("paired_comparison", {})
    require(comparison.get("leader_variant_id") == "v_01", "comparison leader mismatch")
    require(comparison.get("runner_up_variant_id") == "v_02", "runner-up mismatch")
    require(comparison.get("mean_uplift") == 0.2222, "paired uplift mismatch")
    require(comparison.get("uplift_ci95_lower") == -0.0833, "uplift lower bound mismatch")
    require(comparison.get("uplift_ci95_upper") == 0.75, "uplift upper bound mismatch")
    require(comparison.get("ci95_method") == "exhaustive-bootstrap", "uplift method mismatch")
    require(comparison.get("bootstrap_resamples") == 256, "uplift bootstrap count mismatch")
    require(comparison.get("conclusive") is False, "paired comparison must be inconclusive")

    metric = v2["metrics"][0]
    require(metric["name"] == "highest_mean_score", "unexpected V2 metric")
    require(metric["value"] == v1["value"], "V1/V2 value mismatch")
    require(metric["samples"] == v1["samples"], "V1/V2 samples mismatch")
    require(metric["failures"] == 0, "publication contains failures")
    require(v2["execution"]["repeat"] == 1, "execution repeat mismatch")
    require(v2["workload"]["measured_iterations"] == 12, "workload output count mismatch")
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

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in ("0.9365", "0.2222", "-0.0833", "inconclusive"):
        require(expected in readme, f"README is missing benchmark value {expected}")
    require(
        "result_path: benchmarks/publication/prompt-ab-baseline-v2.json" in manifest,
        "manifest V2 path mismatch",
    )

    if args.require_git:
        source_commit = v2["provenance"]["source_commit"]
        require(git_has_commit(source_commit), "source commit unavailable; fetch full history")
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