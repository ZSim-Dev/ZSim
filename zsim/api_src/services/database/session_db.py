"""模拟会话数据库访问层"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column

from zsim.api_src.services.database.orm import Base, get_async_engine, get_async_session
from zsim.models.session.session_create import Session

_session_db: "SessionDB | None" = None


class SessionORM(Base):
    """模拟会话ORM模型"""

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    session_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    create_time: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    session_run: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_result: Mapped[str | None] = mapped_column(Text, nullable=True)


class SessionDB:
    """会话数据库访问对象"""

    def __init__(self) -> None:
        """初始化数据库访问对象"""
        self._cache: dict[str, Any] = {}
        self._db_init = False

    async def _init_db(self) -> None:
        """确保数据库表结构已建立"""
        if self._db_init:
            return
        async with get_async_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._db_init = True

    async def add_session(self, session_data: Session) -> None:
        """添加一个新的模拟会话。

        Args:
            session_data (Session): 会话数据。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        async with get_async_session() as session:
            session.add(
                SessionORM(
                    session_id=session_data.session_id,
                    session_name=session_data.session_name,
                    create_time=session_data.create_time.isoformat(),
                    status=session_data.status,
                    session_run=(
                        session_data.session_run.model_dump_json(indent=4)
                        if session_data.session_run
                        else None
                    ),
                    session_result=(
                        json.dumps(
                            [
                                result.model_dump()
                                for result in session_data.session_result
                            ]
                        )
                        if session_data.session_result
                        else None
                    ),
                )
            )
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def get_session(self, session_id: str) -> Session | None:
        """根据ID获取模拟会话。

        Args:
            session_id (str): 会话ID。

        Returns:
            Session | None: 匹配的会话数据，未找到时返回None。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(SessionORM).where(SessionORM.session_id == session_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return Session(
                session_id=record.session_id,
                session_name=record.session_name,
                create_time=datetime.fromisoformat(record.create_time),
                status=record.status,
                session_run=(
                    json.loads(record.session_run) if record.session_run else None
                ),
                session_result=(
                    json.loads(record.session_result) if record.session_result else None
                ),
            )

    async def update_session(self, session_data: Session) -> None:
        """更新模拟会话。

        Args:
            session_data (Session): 会话数据。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(SessionORM).where(
                    SessionORM.session_id == session_data.session_id
                )
            )
            record = result.scalar_one_or_none()
            if record is None:
                return
            record.session_name = session_data.session_name
            record.create_time = session_data.create_time.isoformat()
            record.status = session_data.status
            record.session_run = (
                session_data.session_run.model_dump_json(indent=4)
                if session_data.session_run
                else None
            )
            record.session_result = (
                json.dumps(
                    [result.model_dump() for result in session_data.session_result]
                )
                if session_data.session_result
                else None
            )
            await session.flush()
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def delete_session(self, session_id: str) -> None:
        """删除模拟会话。

        Args:
            session_id (str): 会话ID。
        """

        await self._init_db()
        async with get_async_session() as session:
            await session.execute(
                delete(SessionORM).where(SessionORM.session_id == session_id)
            )
            await session.commit()

    async def list_sessions(self) -> list[Session]:
        """列出所有模拟会话。

        Returns:
            list[Session]: 会话数据列表。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(SessionORM).order_by(SessionORM.create_time.desc())
            )
            records = result.scalars().all()
        return [
            Session(
                session_id=record.session_id,
                session_name=record.session_name,
                create_time=datetime.fromisoformat(record.create_time),
                status=record.status,
                session_run=(
                    json.loads(record.session_run) if record.session_run else None
                ),
                session_result=(
                    json.loads(record.session_result) if record.session_result else None
                ),
            )
            for record in records
        ]


async def get_session_db() -> SessionDB:
    """获取SessionDB单例。

    Returns:
        SessionDB: 会话数据库访问对象。
    """

    global _session_db
    if _session_db is None:
        _session_db = SessionDB()
    return _session_db
