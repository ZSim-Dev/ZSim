"""Alembic环境配置"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _load_metadata():
    """加载SQLAlchemy元数据"""

    import zsim.api_src.services.database.apl_db  # noqa: F401
    import zsim.api_src.services.database.character_db  # noqa: F401
    import zsim.api_src.services.database.enemy_db  # noqa: F401
    import zsim.api_src.services.database.session_db  # noqa: F401
    from zsim.api_src.services.database.orm import Base

    return Base.metadata


def _get_database_url() -> str:
    """获取同步数据库URL"""

    from zsim.api_src.services.database.orm import get_sync_database_url

    return get_sync_database_url()


target_metadata = _load_metadata()
config.set_main_option("sqlalchemy.url", _get_database_url())


def run_migrations_offline() -> None:
    """Offline模式运行迁移"""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online模式运行迁移"""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
