"""Alembic环境配置"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from zsim.api_src.services.database import (  # noqa: E402  # isort:skip
    apl_db,
    character_db,
    enemy_db,
    session_db,
)
from zsim.api_src.services.database.orm import (  # noqa: E402  # isort:skip
    Base,
    get_sync_database_url,
    get_sync_engine,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
_ = (apl_db, character_db, enemy_db, session_db)


def run_migrations_offline() -> None:
    """Offline模式运行迁移"""

    url = get_sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online模式运行迁移"""

    connectable = get_sync_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
