import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from utils.config import settings

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_URL = settings.database_url

# Handle SQLite relative path if needed
if DATABASE_URL.startswith("sqlite:///./"):
    db_relative = DATABASE_URL.replace("sqlite:///./", "")
    db_path = BASE_DIR / db_relative
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables and seed starter records if needed."""
    from . import models
    from . import repositories
    Base.metadata.create_all(bind=engine)
    repositories.seed_default_data_if_empty()
