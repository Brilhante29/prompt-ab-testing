from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class GenerationValidationError(ValueError):
    """Raised when generation inputs or provider responses are invalid."""


OpenUrl = Callable[[Request, float], Any]


def _open(request: Request, timeout: float) -> Any:
    return urlopen(request, timeout=timeout)


def _sha256(path: str | Path) -> str:
    return f"sha256:{hashlib.sha256(Path(path).read_bytes()).hexdigest()}"


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GenerationValidationError(f"{path}: invalid JSON") from exc
    if not isinstance(value, dict):
        raise GenerationValidationError(f"{path}: expected an object")
    return value


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GenerationValidationError(
                f"{path}:{line_number}: invalid JSON"
            ) from exc
        if not isinstance(record, dict):
            raise GenerationValidationError(
                f"{path}:{line_number}: expected an object"
            )
        records.append(record)
    if not records:
        raise GenerationValidationError(f"{path}: expected at least one record")
    return records


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = expected - value.keys()
    extra = value.keys() - expected
    if missing or extra:
        raise GenerationValidationError(
            f"{label}: missing={sorted(missing)} unexpected={sorted(extra)}"
        )


def load_generation_cases(path: str | Path) -> list[dict[str, str]]:
    records = _read_jsonl(path)
    seen: set[str] = set()
    for index, record in enumerate(records, start=1):
        _exact_keys(record, {"id", "input"}, f"generation_case[{index}]")
        if not isinstance(record["id"], str) or not record["id"].strip():
            raise GenerationValidationError(
                f"generation_case[{index}].id: expected non-empty text"
            )
        if record["id"] in seen:
            raise GenerationValidationError(
                f"generation_case[{index}].id: duplicate ID"
            )
        if not isinstance(record["input"], str) or not record["input"].strip():
            raise GenerationValidationError(
                f"generation_case[{index}].input: expected non-empty text"
            )
        seen.add(record["id"])
    return records  # type: ignore[return-value]


def load_templates(path: str | Path) -> dict[str, dict[str, str]]:
    document = _read_json(path)
    _exact_keys(document, {"schema_version", "templates"}, "templates")
    if document["schema_version"] != 1:
        raise GenerationValidationError("templates.schema_version: expected 1")
    templates = document["templates"]
    if not isinstance(templates, dict) or len(templates) < 2:
        raise GenerationValidationError("templates.templates: expected two or more")
    for variant_id, template in templates.items():
        if not isinstance(variant_id, str) or not isinstance(template, dict):
            raise GenerationValidationError("templates.templates: invalid entry")
        _exact_keys(template, {"system", "user_template"}, f"template[{variant_id}]")
        if not all(
            isinstance(template[field], str) and template[field].strip()
            for field in ("system", "user_template")
        ):
            raise GenerationValidationError(
                f"template[{variant_id}]: fields must be non-empty text"
            )
        if template["user_template"].count("{input}") != 1:
            raise GenerationValidationError(
                f"template[{variant_id}].user_template: expected one {{input}}"
            )
    return templates  # type: ignore[return-value]


class OpenAICompatibleGenerator:
    def __init__(
        self,
        *,
        provider_id: str,
        base_url: str,
        model: str,
        model_digest: str,
        timeout_seconds: float,
        api_key: str | None = None,
        opener: OpenUrl = _open,
    ) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise GenerationValidationError("base URL must be HTTP(S)")
        if parsed.username or parsed.password:
            raise GenerationValidationError("base URL must not contain credentials")
        if timeout_seconds <= 0:
            raise GenerationValidationError("timeout must be positive")
        if not model.strip() or re.fullmatch(r"sha256:[0-9a-f]{64}", model_digest) is None:
            raise GenerationValidationError("model and sha256 digest are required")
        self.provider_id = provider_id
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.model_digest = model_digest
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        self._opener = opener

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        opener: OpenUrl = _open,
    ) -> "OpenAICompatibleGenerator":
        values = os.environ if environment is None else environment
        required = (
            "PROMPT_AB_BASE_URL",
            "PROMPT_AB_MODEL",
            "PROMPT_AB_MODEL_DIGEST",
        )
        missing = [name for name in required if not values.get(name)]
        if missing:
            raise GenerationValidationError(
                "generation requires environment variables: " + ", ".join(missing)
            )
        return cls(
            provider_id=values.get("PROMPT_AB_PROVIDER_ID", "openai-compatible-http"),
            base_url=values["PROMPT_AB_BASE_URL"],
            model=values["PROMPT_AB_MODEL"],
            model_digest=values["PROMPT_AB_MODEL_DIGEST"],
            timeout_seconds=float(values.get("PROMPT_AB_TIMEOUT_SECONDS", "30")),
            api_key=values.get("PROMPT_AB_API_KEY") or None,
            opener=opener,
        )

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
    ) -> tuple[str, dict[str, int]]:
        endpoint = self.base_url
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0,
                "max_tokens": max_tokens,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(endpoint, data=payload, headers=headers, method="POST")
        with self._opener(request, self.timeout_seconds) as response:
            document = json.loads(response.read().decode("utf-8"))
        try:
            output = document["choices"][0]["message"]["content"].strip()
            usage = document["usage"]
            prompt_tokens = int(usage["prompt_tokens"])
            completion_tokens = int(usage["completion_tokens"])
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise GenerationValidationError(
                "provider response must contain non-empty content and exact token usage"
            ) from exc
        if not output:
            raise GenerationValidationError("provider returned empty content")
        return output, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }


def generate_output_matrix(
    *,
    generator: OpenAICompatibleGenerator,
    cases_path: str | Path,
    templates_path: str | Path,
    variant_ids: list[str],
    output_path: str | Path,
    provenance_path: str | Path,
    max_tokens: int = 24,
    warmup_iterations: int = 1,
    producer_source_commit: str = "unverified",
    producer_image_digest: str = "unverified",
) -> dict[str, Any]:
    if max_tokens <= 0 or warmup_iterations < 0:
        raise GenerationValidationError("max tokens and warmup must be non-negative")
    cases = load_generation_cases(cases_path)
    templates = load_templates(templates_path)
    if set(templates) != set(variant_ids):
        raise GenerationValidationError("template IDs must match blinded variant IDs")

    first_case = cases[0]
    first_template = templates[variant_ids[0]]
    for _ in range(warmup_iterations):
        generator.generate(
            system=first_template["system"],
            user=first_template["user_template"].format(input=first_case["input"]),
            max_tokens=max_tokens,
        )

    outputs: list[dict[str, str]] = []
    latencies_ms: list[float] = []
    prompt_tokens = 0
    completion_tokens = 0
    for case in cases:
        for variant_id in variant_ids:
            template = templates[variant_id]
            started = time.perf_counter_ns()
            output, usage = generator.generate(
                system=template["system"],
                user=template["user_template"].format(input=case["input"]),
                max_tokens=max_tokens,
            )
            latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000)
            prompt_tokens += usage["prompt_tokens"]
            completion_tokens += usage["completion_tokens"]
            outputs.append(
                {"case_id": case["id"], "variant_id": variant_id, "output": output}
            )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in outputs),
        encoding="utf-8",
    )
    provenance = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": {
            "id": generator.provider_id,
            "interface": "openai-compatible-chat-completions",
            "model": generator.model,
            "model_digest": generator.model_digest,
        },
        "producer": {
            "source_commit": producer_source_commit,
            "image_digest": producer_image_digest,
        },
        "generation": {
            "temperature": 0,
            "max_tokens": max_tokens,
            "warmup_iterations": warmup_iterations,
            "measured_requests": len(outputs),
            "failures": 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": {
                "mean": round(sum(latencies_ms) / len(latencies_ms), 6),
                "p95": round(_percentile(latencies_ms, 0.95), 6),
            },
        },
        "artifacts": {
            "outputs_sha256": _sha256(output),
            "generation_cases_sha256": _sha256(cases_path),
            "templates_sha256": _sha256(templates_path),
        },
    }
    provenance_output = Path(provenance_path)
    provenance_output.parent.mkdir(parents=True, exist_ok=True)
    provenance_output.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return provenance
