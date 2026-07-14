import argparse
import json
import math
import re
from pathlib import Path

def load_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

def score(answer: str, keywords: list[str], variant: dict) -> float:
    words = set(re.findall(r"[a-z0-9]+", answer.lower()))
    coverage = sum(1 for keyword in keywords if keyword.lower() in words) / len(keywords)
    return max(0.0, min(1.0, coverage * variant["multiplier"] - variant["verbosity_penalty"]))

def mean_ci(values: list[float]) -> tuple[float, float]:
    mean = sum(values) / len(values)
    if len(values) == 1:
        return mean, 0.0
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    ci95 = 1.96 * math.sqrt(variance / len(values))
    return mean, ci95

def evaluate() -> dict:
    cases = load_jsonl("data/fixtures/cases.jsonl")
    variants = json.loads(Path("data/fixtures/variants.json").read_text(encoding="utf-8"))
    rows = []
    for variant in variants:
        scores = [score(case["answer"], case["keywords"], variant) for case in cases]
        avg, ci = mean_ci(scores)
        rows.append({"variant": variant["id"], "name": variant["name"], "score": round(avg, 4), "ci95": round(ci, 4)})
    best = max(rows, key=lambda row: row["score"])
    return {"project": "prompt-ab-testing", "primary_metric": "best_variant_score", "best_variant": best["variant"], "best_variant_score": best["score"], "variants": rows}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["benchmark"], nargs="?", default="benchmark")
    parser.add_argument("--output", default="benchmarks/results/prompt-ab-baseline.json")
    args = parser.parse_args()
    result = evaluate()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
