from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from sqlalchemy import create_engine, pool

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------------------------------
# FIX FOR DOCKER: Add backend directory to PYTHONPATH manually
# ----------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # /app
sys.path.insert(0, str(BASE_DIR))

# Now imports work inside Docker
import database
import models

# Target metadata
target_metadata = database.Base.metadata

# Load DB URL
def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
