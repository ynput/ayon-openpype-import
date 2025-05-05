FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /service
COPY ./pyproject.toml ./uv.lock .

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install -r pyproject.toml --system

COPY processor/ .
CMD ["python", "-m", "processor"]
