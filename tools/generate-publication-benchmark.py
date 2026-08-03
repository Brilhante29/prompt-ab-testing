#!/usr/bin/env python3
"""Produce a schema_version 2 publication benchmark from a real execution.

The v2 contract in tools/validate-portfolio.ps1 requires provenance that cannot
be written by hand: the digest of the image that ran, the digest of the fixture
and config that fed the workload, the commit the tree was on, and the measured
samples. This tool runs the benchmark command, reads the v1 result it produces,
and derives every field from that execution.

It never invents a measurement. If the command fails, or the v1 result is
missing a metric, it exits non-zero and writes nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DIRECTIONS = ("higher_is_better", "lower_is_better", "target")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"



def git_bytes(repo: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={repo}", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout


def git_checked(repo: Path, *args: str) -> str:
    return git_bytes(repo, *args).decode("utf-8").strip()


def digest_committed_path(repo: Path, path: Path, commit: str) -> str:
    """Digest a tracked file or tree from Git blobs, independent of checkout EOLs."""
    relative = path.relative_to(repo).as_posix()
    object_name = f"{commit}:{relative}"
    object_type = git_checked(repo, "cat-file", "-t", object_name)
    if object_type == "blob":
        content = git_bytes(repo, "show", object_name)
        return f"sha256:{hashlib.sha256(content).hexdigest()}"
    if object_type != "tree":
        raise SystemExit(f"unsupported Git object for provenance: {relative} ({object_type})")

    entries = git_bytes(
        repo, "ls-tree", "-r", "-z", "--name-only", commit, "--", relative
    ).split(b"\0")
    digest = hashlib.sha256()
    prefix = f"{relative}/"
    for raw_entry in sorted(entry for entry in entries if entry):
        entry = raw_entry.decode("utf-8")
        if not entry.startswith(prefix):
            raise SystemExit(f"unexpected Git tree entry for {relative}: {entry}")
        digest.update(entry[len(prefix) :].encode("utf-8"))
        digest.update(b"\0")
        digest.update(git_bytes(repo, "show", f"{commit}:{entry}"))
    return f"sha256:{digest.hexdigest()}"


def repo_path(repo: Path, value: Path, label: str) -> Path:
    """Resolve a repo-relative path and reject reads or writes outside the repo."""
    if value.is_absolute():
        raise SystemExit(f"{label} must be relative to the repository: {value}")
    candidate = (repo / value).resolve()
    try:
        candidate.relative_to(repo)
    except ValueError as error:
        raise SystemExit(f"{label} escapes the repository: {value}") from error
    return candidate


def infer_measured_iterations(v1: dict, explicit: int | None) -> int:
    """Return workload size without confusing run repetition with measured work."""
    if explicit is not None:
        if explicit < 1:
            raise SystemExit("--measured-iterations must be at least 1")
        return explicit

    summary = v1.get("summary") if isinstance(v1.get("summary"), dict) else {}
    metrics = v1.get("metrics") if isinstance(v1.get("metrics"), dict) else {}
    environment = v1.get("environment") if isinstance(v1.get("environment"), dict) else {}
    candidates: list[tuple[str, object]] = [
        ("measured_iterations", v1.get("measured_iterations")),
        ("summary.measured_iterations", summary.get("measured_iterations")),
        ("summary.measured_operations", summary.get("measured_operations")),
        ("metrics.total_queries", metrics.get("total_queries")),
        ("metrics.total_plates", metrics.get("total_plates")),
        ("metrics.total_rows", metrics.get("total_rows")),
        ("environment.n_queries", environment.get("n_queries")),
        ("environment.n_plates", environment.get("n_plates")),
    ]
    found: list[tuple[str, int]] = []
    for source, value in candidates:
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, float) and not value.is_integer():
            continue
        if isinstance(value, str) and not value.strip().isdigit():
            continue
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            found.append((source, parsed))

    values = {value for _, value in found}
    if not values:
        raise SystemExit(
            "cannot infer measured iterations from the v1 result; pass "
            "--measured-iterations explicitly"
        )
    if len(values) > 1:
        detail = ", ".join(f"{source}={value}" for source, value in found)
        raise SystemExit(
            f"ambiguous measured iteration counts ({detail}); pass "
            "--measured-iterations explicitly"
        )
    return values.pop()


def image_digest(image: str) -> tuple[str, str]:
    """Return (digest, image_ref) for a locally available image."""
    completed = subprocess.run(
        ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"cannot inspect image {image}: {completed.stderr.strip()}")
    identifier = completed.stdout.strip()
    if not identifier.startswith("sha256:"):
        raise SystemExit(f"unexpected image id for {image}: {identifier}")
    return identifier, f"{image}@{identifier}"


def load_metrics(v1: dict, direction: str) -> list[dict]:
    """Build the v2 metric list from the v1 result the benchmark emitted."""
    name = v1.get("metric")
    if not name or "value" not in v1:
        raise SystemExit("v1 result has no 'metric'/'value'; cannot derive metrics")
    samples = v1.get("samples") or [v1["value"]]
    summary = v1.get("summary") if isinstance(v1.get("summary"), dict) else {name: v1["value"]}
    return [
        {
            "name": name,
            "value": v1["value"],
            "unit": v1.get("unit", "unit"),
            "direction": direction,
            "samples": list(samples),
            "failures": int(v1.get("failures", 0)),
            "summary": summary,
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--project", required=True)
    parser.add_argument("--benchmark-id", required=True)
    parser.add_argument("--image", required=True, help="local image tag that runs the benchmark")
    parser.add_argument("--v1-result", type=Path,
                        help="path (repo-relative) of the v1 JSON the command writes")
    parser.add_argument("--from-container", metavar="NAME:PATH",
                        help="copy the v1 JSON out of a container the command left behind, "
                             "e.g. pub_myrepo:/app/benchmarks/results/latest.json. Use this "
                             "when the image runs as a non-root user and cannot write into a "
                             "bind mount owned by the host user.")
    parser.add_argument("--fixture", required=True, type=Path, help="repo-relative fixture path")
    parser.add_argument("--config", required=True, type=Path, help="repo-relative config path")
    parser.add_argument("--lock", required=True, type=Path, help="repo-relative dependency lock path")
    parser.add_argument("--output", required=True, type=Path, help="repo-relative v2 output path")
    parser.add_argument("--direction", default="higher_is_better", choices=DIRECTIONS)
    parser.add_argument("--workload-version", default="1.0.0")
    parser.add_argument("--warmup-iterations", type=int, default=0)
    parser.add_argument(
        "--measured-iterations",
        type=int,
        help="work items measured in one run; derived only from explicit v1 count fields",
    )
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--runtime", required=True, help="e.g. python-3.12-slim")
    parser.add_argument("--architecture", default="amd64")
    parser.add_argument("--hardware-class", default="docker-local")
    parser.add_argument("--producer", default="local", choices=("local", "github-actions", "other-ci"))
    parser.add_argument("--comparability-key", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900,
                        help="abort if the benchmark does not finish. Without this a command "
                             "that starts a server instead of a benchmark hangs forever.")
    # The benchmark command comes last, after "--", so its own flags are never
    # confused with this tool's options.
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="-- <command to execute>")
    args = parser.parse_args()

    repo: Path = args.repo.resolve()
    if not repo.is_dir():
        raise SystemExit(f"repository does not exist: {repo}")
    if args.warmup_iterations < 0:
        raise SystemExit("--warmup-iterations cannot be negative")
    if args.concurrency < 1:
        raise SystemExit("--concurrency must be at least 1")
    if args.timeout_seconds < 1:
        raise SystemExit("--timeout-seconds must be at least 1")

    source_commit = git_checked(repo, "rev-parse", "HEAD")
    if len(source_commit) != 40:
        raise SystemExit(f"unexpected source commit: {source_commit}")
    if git_checked(repo, "status", "--porcelain"):
        raise SystemExit("repository must be clean before generating publication evidence")

    fixture_path = repo_path(repo, args.fixture, "--fixture")
    config_path = repo_path(repo, args.config, "--config")
    lock_path = repo_path(repo, args.lock, "--lock")
    output = repo_path(repo, args.output, "--output")
    for label, path in (
        ("--fixture", fixture_path),
        ("--config", config_path),
        ("--lock", lock_path),
    ):
        if not path.exists():
            raise SystemExit(f"{label} does not exist: {path.relative_to(repo)}")

    command = [part for part in args.command if part != "--"]
    if not command:
        raise SystemExit("pass the benchmark command after '--'")

    digest, image_ref = image_digest(args.image)
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                                   check=False, timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"benchmark did not finish in {args.timeout_seconds}s. If the image's default "
            f"command starts a server, pass the benchmark subcommand explicitly."
        )
    duration = time.perf_counter() - clock

    if completed.returncode != 0:
        sys.stderr.write(completed.stdout[-2000:])
        sys.stderr.write(completed.stderr[-2000:])
        raise SystemExit(f"benchmark command exited {completed.returncode}; no result written")

    if args.from_container:
        if not args.v1_result:
            raise SystemExit("--from-container also needs --v1-result as the destination path")
        v1_path = repo_path(repo, args.v1_result, "--v1-result")
        v1_path.parent.mkdir(parents=True, exist_ok=True)
        copy = subprocess.run(
            ["docker", "cp", args.from_container, str(v1_path)],
            capture_output=True, text=True, check=False,
        )
        if copy.returncode != 0:
            raise SystemExit(f"cannot copy {args.from_container}: {copy.stderr.strip()}")
    elif args.v1_result:
        v1_path = repo_path(repo, args.v1_result, "--v1-result")
    else:
        raise SystemExit("pass --v1-result (optionally with --from-container)")

    if not v1_path.is_file():
        raise SystemExit(f"benchmark did not produce {args.v1_result}")
    try:
        v1 = json.loads(v1_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read v1 result {args.v1_result}: {error}") from error

    measured_iterations = infer_measured_iterations(v1, args.measured_iterations)
    repeat = max(1, int(v1.get("repeat", 1)))
    result = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "project": args.project,
        "benchmark_id": args.benchmark_id,
        "workload": {
            "version": args.workload_version,
            "fixture_digest": digest_committed_path(repo, fixture_path, source_commit),
            "config_digest": digest_committed_path(repo, config_path, source_commit),
            "warmup_iterations": args.warmup_iterations,
            "measured_iterations": measured_iterations,
            "concurrency": args.concurrency,
        },
        "metrics": load_metrics(v1, args.direction),
        "execution": {
            "command": shlex.join(command),
            "started_at": started.isoformat().replace("+00:00", "Z"),
            "duration_seconds": round(duration, 6),
            "exit_code": completed.returncode,
            "repeat": repeat,
        },
        "environment": {
            "runtime": args.runtime,
            "architecture": args.architecture,
            "hardware_class": args.hardware_class,
        },
        "provenance": {
            "source_commit": source_commit,
            "clean_tree": True,
            "image_ref": image_ref,
            "image_digest": digest,
            "dependency_lock_digest": digest_committed_path(repo, lock_path, source_commit),
            "producer": args.producer,
            "artifact_digest": sha256_file(v1_path),
        },
        "comparability_key": args.comparability_key,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} run_id={result['run_id']} metric={result['metrics'][0]['name']}"
          f"={result['metrics'][0]['value']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
