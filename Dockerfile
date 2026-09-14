FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

RUN apt-get update && apt-get upgrade --yes && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser data ./data
COPY --chown=appuser:appuser benchmarks ./benchmarks

USER appuser

ENTRYPOINT ["python", "-m", "prompt_ab_testing"]
CMD ["benchmark", "--output", "benchmarks/results/prompt-ab-baseline.json"]
