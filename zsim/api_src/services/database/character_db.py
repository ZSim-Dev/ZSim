"""角色配置数据库访问层"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Float, Integer, String, Text, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column

from zsim.api_src.services.database.orm import Base, get_async_engine, get_async_session
from zsim.models.character.character_config import CharacterConfig

_character_db: "CharacterDB | None" = None


class CharacterConfigORM(Base):

    __tablename__ = "character_configs"

    config_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weapon: Mapped[str] = mapped_column(String(255), nullable=False)
    weapon_level: Mapped[int] = mapped_column(Integer, nullable=False)
    cinema: Mapped[int] = mapped_column(Integer, nullable=False)
    crit_balancing: Mapped[bool] = mapped_column(Boolean, nullable=False)
    crit_rate_limit: Mapped[float] = mapped_column(Float, nullable=False)
    scATK_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    scATK: Mapped[int] = mapped_column(Integer, nullable=False)
    scHP_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    scHP: Mapped[int] = mapped_column(Integer, nullable=False)
    scDEF_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    scDEF: Mapped[int] = mapped_column(Integer, nullable=False)
    scAnomalyProficiency: Mapped[int] = mapped_column(Integer, nullable=False)
    scPEN: Mapped[int] = mapped_column(Integer, nullable=False)
    scCRIT: Mapped[int] = mapped_column(Integer, nullable=False)
    scCRIT_DMG: Mapped[int] = mapped_column(Integer, nullable=False)
    drive4: Mapped[str] = mapped_column(Text, nullable=False)
    drive5: Mapped[str] = mapped_column(Text, nullable=False)
    drive6: Mapped[str] = mapped_column(Text, nullable=False)
    equip_style: Mapped[str] = mapped_column(String(255), nullable=False)
    equip_set4: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equip_set2_a: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equip_set2_b: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equip_set2_c: Mapped[str | None] = mapped_column(String(255), nullable=True)
    create_time: Mapped[str] = mapped_column(String(32), nullable=False)
    update_time: Mapped[str] = mapped_column(String(32), nullable=False)


class CharacterDB:
    """角色配置数据库访问对象"""

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

    async def add_character_config(self, config: CharacterConfig) -> None:
        """添加一个新的角色配置。

        Args:
            config (CharacterConfig): 角色配置数据。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        if not config.config_id:
            config.config_id = f"{config.name}_{config.config_name}"
        config.update_time = datetime.now()

        async with get_async_session() as session:
            session.add(
                CharacterConfigORM(
                    config_id=config.config_id,
                    name=config.name,
                    config_name=config.config_name,
                    weapon=config.weapon,
                    weapon_level=config.weapon_level,
                    cinema=config.cinema,
                    crit_balancing=config.crit_balancing,
                    crit_rate_limit=config.crit_rate_limit,
                    scATK_percent=config.scATK_percent,
                    scATK=config.scATK,
                    scHP_percent=config.scHP_percent,
                    scHP=config.scHP,
                    scDEF_percent=config.scDEF_percent,
                    scDEF=config.scDEF,
                    scAnomalyProficiency=config.scAnomalyProficiency,
                    scPEN=config.scPEN,
                    scCRIT=config.scCRIT,
                    scCRIT_DMG=config.scCRIT_DMG,
                    drive4=config.drive4,
                    drive5=config.drive5,
                    drive6=config.drive6,
                    equip_style=config.equip_style,
                    equip_set4=config.equip_set4,
                    equip_set2_a=config.equip_set2_a,
                    equip_set2_b=config.equip_set2_b,
                    equip_set2_c=config.equip_set2_c,
                    create_time=config.create_time.isoformat(),
                    update_time=config.update_time.isoformat(),
                )
            )
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def get_character_config(
        self, name: str, config_name: str
    ) -> CharacterConfig | None:
        """根据角色名称和配置名称获取角色配置。

        Args:
            name (str): 角色名称。
            config_name (str): 配置名称。

        Returns:
            CharacterConfig | None: 匹配的角色配置，未找到时返回None。
        """

        await self._init_db()
        config_id = f"{name}_{config_name}"
        async with get_async_session() as session:
            result = await session.execute(
                select(CharacterConfigORM).where(
                    CharacterConfigORM.config_id == config_id
                )
            )
            record = result.scalar_one_or_none()
            if record is None:
                return None
            return CharacterConfig(
                config_id=record.config_id,
                name=record.name,
                config_name=record.config_name,
                weapon=record.weapon,
                weapon_level=record.weapon_level,
                cinema=record.cinema,
                crit_balancing=record.crit_balancing,
                crit_rate_limit=record.crit_rate_limit,
                scATK_percent=record.scATK_percent,
                scATK=record.scATK,
                scHP_percent=record.scHP_percent,
                scHP=record.scHP,
                scDEF_percent=record.scDEF_percent,
                scDEF=record.scDEF,
                scAnomalyProficiency=record.scAnomalyProficiency,
                scPEN=record.scPEN,
                scCRIT=record.scCRIT,
                scCRIT_DMG=record.scCRIT_DMG,
                drive4=record.drive4,
                drive5=record.drive5,
                drive6=record.drive6,
                equip_style=record.equip_style,
                equip_set4=record.equip_set4,
                equip_set2_a=record.equip_set2_a,
                equip_set2_b=record.equip_set2_b,
                equip_set2_c=record.equip_set2_c,
                create_time=datetime.fromisoformat(record.create_time),
                update_time=datetime.fromisoformat(record.update_time),
            )

    async def update_character_config(self, config: CharacterConfig) -> None:
        """更新数据库中的角色配置。

        Args:
            config (CharacterConfig): 新的角色配置信息。

        Raises:
            SQLAlchemyError: 当数据库写入失败时抛出。
        """

        await self._init_db()
        config.update_time = datetime.now()

        async with get_async_session() as session:
            result = await session.execute(
                select(CharacterConfigORM).where(
                    CharacterConfigORM.config_id == config.config_id
                )
            )
            record = result.scalar_one_or_none()
            if record is None:
                return
            record.name = config.name
            record.config_name = config.config_name
            record.weapon = config.weapon
            record.weapon_level = config.weapon_level
            record.cinema = config.cinema
            record.crit_balancing = config.crit_balancing
            record.crit_rate_limit = config.crit_rate_limit
            record.scATK_percent = config.scATK_percent
            record.scATK = config.scATK
            record.scHP_percent = config.scHP_percent
            record.scHP = config.scHP
            record.scDEF_percent = config.scDEF_percent
            record.scDEF = config.scDEF
            record.scAnomalyProficiency = config.scAnomalyProficiency
            record.scPEN = config.scPEN
            record.scCRIT = config.scCRIT
            record.scCRIT_DMG = config.scCRIT_DMG
            record.drive4 = config.drive4
            record.drive5 = config.drive5
            record.drive6 = config.drive6
            record.equip_style = config.equip_style
            record.equip_set4 = config.equip_set4
            record.equip_set2_a = config.equip_set2_a
            record.equip_set2_b = config.equip_set2_b
            record.equip_set2_c = config.equip_set2_c
            record.update_time = config.update_time.isoformat()
            await session.flush()
            try:
                await session.commit()
            except SQLAlchemyError as exc:  # noqa: BLE001
                await session.rollback()
                raise exc

    async def delete_character_config(self, name: str, config_name: str) -> None:
        """删除指定角色的配置。

        Args:
            name (str): 角色名称。
            config_name (str): 配置名称。
        """

        await self._init_db()
        config_id = f"{name}_{config_name}"
        async with get_async_session() as session:
            await session.execute(
                delete(CharacterConfigORM).where(
                    CharacterConfigORM.config_id == config_id
                )
            )
            await session.commit()

    async def list_character_configs(self, name: str) -> list[CharacterConfig]:
        """获取指定角色的所有配置列表。

        Args:
            name (str): 角色名称。

        Returns:
            list[CharacterConfig]: 角色配置列表。
        """

        await self._init_db()
        async with get_async_session() as session:
            result = await session.execute(
                select(CharacterConfigORM)
                .where(CharacterConfigORM.name == name)
                .order_by(CharacterConfigORM.config_name)
            )
            records = result.scalars().all()
        return [
            CharacterConfig(
                config_id=record.config_id,
                name=record.name,
                config_name=record.config_name,
                weapon=record.weapon,
                weapon_level=record.weapon_level,
                cinema=record.cinema,
                crit_balancing=record.crit_balancing,
                crit_rate_limit=record.crit_rate_limit,
                scATK_percent=record.scATK_percent,
                scATK=record.scATK,
                scHP_percent=record.scHP_percent,
                scHP=record.scHP,
                scDEF_percent=record.scDEF_percent,
                scDEF=record.scDEF,
                scAnomalyProficiency=record.scAnomalyProficiency,
                scPEN=record.scPEN,
                scCRIT=record.scCRIT,
                scCRIT_DMG=record.scCRIT_DMG,
                drive4=record.drive4,
                drive5=record.drive5,
                drive6=record.drive6,
                equip_style=record.equip_style,
                equip_set4=record.equip_set4,
                equip_set2_a=record.equip_set2_a,
                equip_set2_b=record.equip_set2_b,
                equip_set2_c=record.equip_set2_c,
                create_time=datetime.fromisoformat(record.create_time),
                update_time=datetime.fromisoformat(record.update_time),
            )
            for record in records
        ]


async def get_character_db() -> CharacterDB:
    """获取CharacterDB单例。

    Returns:
        CharacterDB: 单例数据库访问对象。
    """

    global _character_db
    if _character_db is None:
        _character_db = CharacterDB()
    return _character_db
