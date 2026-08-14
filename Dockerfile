# syntax=docker/dockerfile:1
#
# Builder is python:3.11-slim-bookworm and the runtime is
# distroless/python3-debian12:nonroot - both ship Python 3.11 on Debian 12,
# which must stay paired since distroless has no package manager to fix an
# ABI mismatch at runtime. Bumping to Python 3.13 (python3-debian13) is a
# separate stack upgrade, out of scope here.

FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --target /deps -r requirements.txt


FROM gcr.io/distroless/python3-debian12:nonroot

ENV PYTHONPATH=/deps \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /deps /deps
COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/bin/python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"]

ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "app/core/uvicorn_log_config.json"]
