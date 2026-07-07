#!/usr/bin/env bash
# Render build script for the AnnotateX backend.
# Runs from the repository root (where pyproject.toml / uv.lock live).
set -o errexit

# Install uv, then the locked dependencies into a project virtualenv.
pip install --upgrade uv
uv sync --frozen

# Collect static files (served by WhiteNoise) and apply DB migrations.
uv run python backend/manage.py collectstatic --no-input
uv run python backend/manage.py migrate
