#!/usr/bin/env bash
# Quickstart script for LogisticsUpdate AI

cd "$(dirname "$0")"

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python run.py
