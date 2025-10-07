"""敌人配置数据库访问层"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Integer, String, Text, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column

from zsim.api_src.services.database.orm import Base, get_async_engine, get_async_session
from zsim.models.enemy.enemy_config import EnemyConfig

_enemy_db: "EnemyDB | None" = None


class EnemyConfigORM(Base):

    __tablename__ = "enemy_configs"

    config_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    enemy_index: Mapped[int] = mapped_column(Integer, nullable=False)
    enemy_adjust: Mapped[str] = mapped_column(Text, nullable=False)
    create_time: Mapped[str] = mapped_column(String(32), nullable=False)
    update_time: Mapped[str] = mapped_column(String(32), nullable=False)


class EnemyDB:
    """敌人配置数据库访问对象"""

    def __init__(self) -> None:
        """初始化数据库访问对象"""
        self._db_init = False

    async def _init_db(self) -> None:
        """确保数据库表结构已建立"""
        if self._db_init:
            return
        async with get_async_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._db_init = True

    async def add_enemy_config(self, config: EnemyConfig) -> None:
        """添加敌人配置。

        Args:
            config (EnemyConfig): 敌人配置数据。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        config.update_time = datetime.now()
        async with get_async_session() as session:
            session.add(
                EnemyConfigORM(
                    config_id=config.config_id,
                    enemy_index=config.enemy_index,
                    enemy_adjust=json.dumps(config.enemy_adjust),
                    create_time=config.create_time.isoformat(),
                    update_time=config.update_time.isoformat(),
                )
            )
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def get_enemy_config(self, config_id: str) -> EnemyConfig | None:
        """根据配置ID获取敌人配置。

        Args:
            config_id (str): 敌人配置ID。

        Returns:
            EnemyConfig | None: 匹配的敌人配置，未找到时返回None。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(EnemyConfigORM).where(EnemyConfigORM.config_id == config_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return EnemyConfig(
                config_id=record.config_id,
                enemy_index=record.enemy_index,
                enemy_adjust=json.loads(record.enemy_adjust),
                create_time=datetime.fromisoformat(record.create_time),
                update_time=datetime.fromisoformat(record.update_time),
            )

    async def update_enemy_config(self, config: EnemyConfig) -> None:
        """更新敌人配置。

        Args:
            config (EnemyConfig): 敌人配置数据。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        config.update_time = datetime.now()
        async with get_async_session() as session:
            result = await session.execute(
                select(EnemyConfigORM).where(
                    EnemyConfigORM.config_id == config.config_id
                )
            )
            record = result.scalar_one_or_none()
            if record is None:
                return
            record.enemy_index = config.enemy_index
            record.enemy_adjust = json.dumps(config.enemy_adjust)
            record.update_time = config.update_time.isoformat()
            await session.flush()
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def delete_enemy_config(self, config_id: str) -> None:
        """删除敌人配置。

        Args:
            config_id (str): 敌人配置ID。
        """

        await self._init_db()
        async with get_async_session() as session:
            await session.execute(
                delete(EnemyConfigORM).where(EnemyConfigORM.config_id == config_id)
            )
            await session.commit()

    async def list_enemy_configs(self) -> list[EnemyConfig]:
        """列出所有敌人配置。

        Returns:
            list[EnemyConfig]: 敌人配置列表。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(EnemyConfigORM).order_by(EnemyConfigORM.config_id)
            )
            records = result.scalars().all()
        return [
            EnemyConfig(
                config_id=record.config_id,
                enemy_index=record.enemy_index,
                enemy_adjust=json.loads(record.enemy_adjust),
                create_time=datetime.fromisoformat(record.create_time),
                update_time=datetime.fromisoformat(record.update_time),
            )
            for record in records
        ]


async def get_enemy_db() -> EnemyDB:
    """获取EnemyDB单例。

    Returns:
        EnemyDB: 敌人数据库访问对象。
    """

    global _enemy_db
    if _enemy_db is None:
        _enemy_db = EnemyDB()
    return _enemy_db
