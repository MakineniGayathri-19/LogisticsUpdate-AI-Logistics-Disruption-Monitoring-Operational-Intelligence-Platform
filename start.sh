#!/usr/bin/env bash
# Start FastAPI backend in background
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Start Streamlit frontend on Render's dynamic PORT
streamlit run app/frontend.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true
