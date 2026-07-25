# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --target /deps -r requirements.txt


FROM gcr.io/distroless/python3-debian12:nonroot

ENV PYTHONPATH=/deps
WORKDIR /app

COPY --from=builder /deps /deps
COPY app/ ./app/

EXPOSE 8000

ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "app/core/uvicorn_log_config.json"]
