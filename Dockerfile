FROM ghcr.io/astral-sh/uv:0.9.28-python3.11-bookworm-slim@sha256:0b378bcc66249d04d6b43162071936a55e5076d071f37157a9ae48731f296e16 AS build
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY src ./src
FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3 AS runtime
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY src ./src
ENV PATH=/app/.venv/bin:$PATH PYTHONPATH=/app/src
USER app
CMD ["python", "-m", "researchops"]
