"""Utilities for programmatically running Alembic migrations."""

from __future__ import annotations

from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from importlib.resources import as_file, files

from zsim.api_src.services.database.orm import get_sync_database_url, get_sync_engine


@contextmanager
def _alembic_cfg() -> Config:
    """构造指向包内迁移脚本的Alembic配置。"""

    script_location = files("zsim.api_src.services.database.migrations")
    with as_file(script_location) as script_dir:
        cfg = Config()
        cfg.set_main_option("script_location", str(script_dir))
        cfg.set_main_option("sqlalchemy.url", get_sync_database_url())
        yield cfg


def run_migrations_to_head() -> None:
    """确保数据库结构升级到最新版本。"""

    # 初始化同步引擎以确保数据库文件和目录已创建
    get_sync_engine()
    with _alembic_cfg() as cfg:
        command.upgrade(cfg, "head")


__all__ = ["run_migrations_to_head"]
