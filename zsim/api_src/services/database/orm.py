"""SQLAlchemy基础设施定义"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from zsim.define import SQLITE_PATH


class Base(DeclarativeBase):
    """声明式基类"""


def _database_path() -> Path:
    """返回SQLite数据库路径。

    Returns:
        Path: 数据库文件的绝对路径。
    """

    path = Path(SQLITE_PATH).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def get_async_database_url() -> str:
    """获取异步模式下的数据库URL。

    Returns:
        str: 适用于异步SQLAlchemy引擎的数据库URL。
    """

    return f"sqlite+aiosqlite:///{_database_path().as_posix()}"


def get_sync_database_url() -> str:
    """获取同步模式下的数据库URL。

    Returns:
        str: 适用于同步SQLAlchemy引擎（如Alembic）的数据库URL。
    """

    return f"sqlite:///{_database_path().as_posix()}"


_async_engine: AsyncEngine = create_async_engine(get_async_database_url(), future=True)
_async_session_factory = async_sessionmaker(_async_engine, expire_on_commit=False)
_sync_engine: Engine | None = None


def get_async_engine() -> AsyncEngine:
    """返回复用的异步SQLAlchemy引擎实例。

    Returns:
        AsyncEngine: 进程范围内复用的异步引擎。
    """

    return _async_engine


def get_sync_engine() -> Engine:
    """返回复用的同步SQLAlchemy引擎实例。"""

    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(get_sync_database_url(), future=True)
    return _sync_engine


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """获取一个SQLAlchemy异步会话。

    Returns:
        AsyncIterator[AsyncSession]: SQLAlchemy异步会话上下文管理器。

    Raises:
        RuntimeError: 当执行过程中出现数据库错误时抛出。
    """

    session = _async_session_factory()
    try:
        yield session
    except Exception as exc:
        await session.rollback()
        raise RuntimeError("异步数据库会话执行失败") from exc
    finally:
        await session.close()


__all__ = [
    "Base",
    "get_async_engine",
    "get_async_session",
    "get_async_database_url",
    "get_sync_database_url",
    "get_sync_engine",
]
