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
    # Operating mode
    mode: str = os.getenv("APP_MODE", "demo").lower()

    # Web Scraping: Firecrawl
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")

    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Memento Memory Service
    memento_api_key: str = os.getenv("MEMENTO_API_KEY", "")
    memento_api_url: str = os.getenv("MEMENTO_API_URL", "https://api.memento.ai/v1")

    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'database' / 'app.db'}")

    # API Connection
    api_base_url: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

    @property
    def is_firecrawl_active(self) -> bool:
        return bool(self.firecrawl_api_key and len(self.firecrawl_api_key.strip()) > 5)

    @property
    def is_llm_active(self) -> bool:
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key and len(self.gemini_api_key.strip()) > 5)
        return bool(self.openai_api_key and len(self.openai_api_key.strip()) > 5)

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
