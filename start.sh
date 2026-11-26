#!/usr/bin/env bash
# Serve the FastAPI API and dashboard from the same process.
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
