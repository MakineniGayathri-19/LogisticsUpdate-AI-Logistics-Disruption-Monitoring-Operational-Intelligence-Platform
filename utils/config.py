"""Utility configuration module for LogisticsUpdate AI.
Loads environment variables safely and provides structured Settings.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
# Load .env if present
load_dotenv(BASE_DIR / ".env")

@dataclass
class Settings:
    # Web Scraping: Firecrawl
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")

    # Memento Memory Service
    memento_api_key: str = os.getenv("MEMENTO_API_KEY", "")
    memento_api_url: str = os.getenv("MEMENTO_API_URL", "https://api.memento.ai/v1")

    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'app.db'}")

    @property
    def is_firecrawl_active(self) -> bool:
        return bool(self.firecrawl_api_key and len(self.firecrawl_api_key.strip()) > 5)

    @property
    def is_memento_active(self) -> bool:
        return bool(self.memento_api_key and len(self.memento_api_key.strip()) > 5)

    @staticmethod
    def mask_key(key: str) -> str:
        """Safely mask API key for UI and logs without exposing secrets."""
        if not key or len(key.strip()) < 8:
            return "Not Configured"
        k = key.strip()
        return f"{k[:4]}...{k[-4:]}"

settings = Settings()
