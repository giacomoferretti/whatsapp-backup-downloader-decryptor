FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Use the system interpreter, which is at the same path in the final image
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
# Install the project as a regular package, so the final image only needs .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.13-alpine

RUN adduser -D -u 1000 app && mkdir /data && chown app:app /data

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Mount a host directory here; tokens, backups and keys are read from and
# written to the working directory
WORKDIR /data
USER 1000:1000

ENTRYPOINT ["wabdd"]
