#!/usr/bin/env bash

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

if ! command -v poetry >/dev/null 2>&1; then
  curl -sSL https://install.python-poetry.org | python3 -
fi

poetry config virtualenvs.in-project true
poetry install --no-root

if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
fi