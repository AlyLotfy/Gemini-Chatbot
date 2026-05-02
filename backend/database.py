from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Single source of truth for DB URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'chat.db').as_posix()}",
)

# SQLite needs this flag; other DBs do not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global metadata for all models (used by Alembic)
Base = declarative_base()
