# Ubuntu image for running the Maida gate and app tests on Windows hosts.
# Bind-mount the checkout at /workspace; the synced environment lives at /opt/venv
# so host files do not replace the Linux virtualenv.
FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY . .
RUN uv sync --locked

CMD ["uv", "run", "--frozen", "python", "github_gate.py"]
