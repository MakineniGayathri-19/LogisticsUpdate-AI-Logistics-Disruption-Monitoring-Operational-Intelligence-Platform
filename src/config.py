"""Configuration module
Loads environment variables and defines constants used across the project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Firecrawl API key – required for data collection
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# LLM – OpenAI (or Gemini) API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Optional Gemini key – uncomment if you switch provider
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Sources – list of URLs (or RSS, API endpoints) to monitor
# Add or remove entries as needed for your domain
SOURCES = [
    "https://www.portofrotterdam.com/en/news",
    "https://www.weather.gov/",
    "https://www.marinetraffic.com/en/ais-home/",
    # Add more public logistics sources here
]

# Directory paths (all relative to project root)
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
MEMENTO_REPO_DIR = PROJECT_ROOT / "memento_repo"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist at runtime
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MEMENTO_REPO_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
