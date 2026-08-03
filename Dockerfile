FROM python:3.12.13-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

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
