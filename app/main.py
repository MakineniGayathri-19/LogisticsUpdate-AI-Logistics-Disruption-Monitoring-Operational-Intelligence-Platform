"""FastAPI application entrypoint for LogisticsUpdate AI backend.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from backend.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed demo data on startup
    init_db()
    yield

app = FastAPI(
    title="LogisticsUpdate AI Backend",
    description="Operational Intelligence Platform API for Maritime & Supply Chain Disruption Monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "platform": "LogisticsUpdate AI",
        "description": "AI-Powered Logistics Disruption Monitoring & Operational Intelligence",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
