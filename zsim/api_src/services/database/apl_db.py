"""
APL数据库服务
负责APL相关数据的数据库操作
"""

from __future__ import annotations

import asyncio
import os
import tomllib
import uuid
from datetime import datetime
from typing import Any

import tomli_w
from sqlalchemy import String, Text, delete, select
from sqlalchemy.orm import Mapped, mapped_column

from zsim.api_src.services.database.orm import Base, get_async_engine, get_async_session
from zsim.define import COSTOM_APL_DIR, DEFAULT_APL_DIR


class APLConfigORM(Base):
    __tablename__ = "apl_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[str] = mapped_column(String(32), nullable=False)
    latest_change_time: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class APLDatabase:
    """APL数据库操作类"""

    def __init__(self) -> None:
        """初始化APL数据库实例"""
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """确保数据库元数据已创建"""
        if self._initialized:
            return
        async with get_async_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    def get_apl_templates(self) -> list[dict[str, Any]]:
        """获取所有APL模板。

        Returns:
            list[dict[str, Any]]: 模板信息列表。
        """

        templates = []
        templates.extend(self._get_apl_from_dir(DEFAULT_APL_DIR, "default"))
        templates.extend(self._get_apl_from_dir(COSTOM_APL_DIR, "custom"))
        return templates

    def get_apl_config(self, config_id: str) -> dict[str, Any] | None:
        """获取特定APL配置。

        Args:
            config_id (str): APL配置ID。

        Returns:
            dict[str, Any] | None: APL配置内容，未找到时返回None。
        """
        if not config_id or not isinstance(config_id, str):
            return None

        return asyncio.get_event_loop().run_until_complete(self._get_apl_config_async(config_id))

    async def _get_apl_config_async(self, config_id: str) -> dict[str, Any] | None:
        """异步获取特定APL配置。

        Args:
            config_id (str): APL配置ID。

        Returns:
            dict[str, Any] | None: APL配置内容，未找到时返回None。
        """

        await self._ensure_initialized()
        async with get_async_session() as session:
            result = await session.execute(select(APLConfigORM).where(APLConfigORM.id == config_id))
            record = result.scalar_one_or_none()
            if record is None:
                return None
            content = tomllib.loads(record.content)
            return {
                "title": record.title,
                "author": record.author,
                "comment": record.comment,
                "create_time": record.create_time,
                "latest_change_time": record.latest_change_time,
                **content,
            }

    def create_apl_config(self, config_data: dict[str, Any]) -> str:
        """创建新的APL配置。

        Args:
            config_data (dict[str, Any]): APL配置数据。

        Returns:
            str: 新建配置的ID。

        Raises:
            Exception: 当写入数据库失败时抛出。
        """
        if not config_data or not isinstance(config_data, dict):
            raise ValueError("配置数据不能为空且必须是字典类型")

        config_id = str(uuid.uuid4())
        asyncio.get_event_loop().run_until_complete(
            self._create_apl_config_async(config_id, config_data)
        )
        return config_id

    async def _create_apl_config_async(self, config_id: str, config_data: dict[str, Any]) -> None:
        """异步创建APL配置。

        Args:
            config_id (str): 新配置ID。
            config_data (dict[str, Any]): APL配置数据。
        """

        await self._ensure_initialized()
        current_time = datetime.now().isoformat()
        title = config_data.get("title", "")
        author = config_data.get("author", "")
        comment = config_data.get("comment", "")
        content_data = config_data.copy()
        content_data.pop("title", None)
        content_data.pop("author", None)
        content_data.pop("comment", None)
        content_data.pop("create_time", None)
        content_data.pop("latest_change_time", None)
        content = tomli_w.dumps(content_data)

        async with get_async_session() as session:
            session.add(
                APLConfigORM(
                    id=config_id,
                    title=title,
                    author=author,
                    comment=comment,
                    create_time=current_time,
                    latest_change_time=current_time,
                    content=content,
                )
            )
            await session.commit()

    def update_apl_config(self, config_id: str, config_data: dict[str, Any]) -> bool:
        """更新APL配置。

        Args:
            config_id (str): APL配置ID。
            config_data (dict[str, Any]): 更新后的数据。

        Returns:
            bool: 更新成功返回True，否则False。
        """
        if not config_id or not isinstance(config_id, str):
            return False
        if not config_data or not isinstance(config_data, dict):
            return False

        return asyncio.get_event_loop().run_until_complete(
            self._update_apl_config_async(config_id, config_data)
        )

    async def _update_apl_config_async(self, config_id: str, config_data: dict[str, Any]) -> bool:
        """异步更新APL配置。

        Args:
            config_id (str): APL配置ID。
            config_data (dict[str, Any]): 更新后的数据。

        Returns:
            bool: 更新成功返回True，否则False。
        """

        await self._ensure_initialized()
        async with get_async_session() as session:
            result = await session.execute(select(APLConfigORM).where(APLConfigORM.id == config_id))
            record = result.scalar_one_or_none()
            if record is None:
                return False

            latest_change_time = datetime.now().isoformat()
            record.title = config_data.get("title", "")
            record.author = config_data.get("author", "")
            record.comment = config_data.get("comment", "")
            record.latest_change_time = latest_change_time

            content_data = config_data.copy()
            content_data.pop("title", None)
            content_data.pop("author", None)
            content_data.pop("comment", None)
            content_data.pop("create_time", None)
            content_data.pop("latest_change_time", None)
            record.content = tomli_w.dumps(content_data)

            await session.flush()
            await session.commit()
            return True

    def delete_apl_config(self, config_id: str) -> bool:
        """删除APL配置。

        Args:
            config_id (str): APL配置ID。

        Returns:
            bool: 删除成功返回True，否则False。
        """
        if not config_id or not isinstance(config_id, str):
            return False

        return asyncio.get_event_loop().run_until_complete(self._delete_apl_config_async(config_id))

    async def _delete_apl_config_async(self, config_id: str) -> bool:
        """异步删除APL配置。

        Args:
            config_id (str): APL配置ID。

        Returns:
            bool: 删除成功返回True，否则False。
        """

        await self._ensure_initialized()
        async with get_async_session() as session:
            result = await session.execute(delete(APLConfigORM).where(APLConfigORM.id == config_id))
            if result.rowcount == 0:
                await session.rollback()
                return False
            await session.commit()
            return True

    def export_apl_config(self, config_id: str, file_path: str) -> bool:
        """导出APL配置到TOML文件。

        Args:
            config_id (str): APL配置ID。
            file_path (str): 导出文件路径。

        Returns:
            bool: 导出成功返回True，否则False。
        """
        if not config_id or not isinstance(config_id, str):
            return False
        if not file_path or not isinstance(file_path, str):
            return False

        config = self.get_apl_config(config_id)
        if config is None:
            return False

        export_data = config.copy()
        export_data.pop("create_time", None)
        export_data.pop("latest_change_time", None)

        # 确保目标目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 使用tomli_w.dump写入文件对象
        with open(file_path, "wb") as file:
            tomli_w.dump(export_data, file)
        return True

    def import_apl_config(self, file_path: str) -> str | None:
        """从TOML文件导入APL配置。

        Args:
            file_path (str): APL文件路径。

        Returns:
            str | None: 导入成功时返回新配置ID，否则None。
        """
        if not file_path or not isinstance(file_path, str):
            return None
        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as file:
            config_data = tomllib.load(file)

        config_id = str(uuid.uuid4())
        asyncio.get_event_loop().run_until_complete(
            self._create_apl_config_async(config_id, config_data)
        )
        return config_id

    def get_apl_files(self) -> list[dict[str, Any]]:
        """获取所有APL文件列表。

        Returns:
            list[dict[str, Any]]: APL文件信息列表。
        """

        files = []
        files.extend(self._get_apl_files_from_dir(DEFAULT_APL_DIR, "default"))
        files.extend(self._get_apl_files_from_dir(COSTOM_APL_DIR, "custom"))
        return files

    def get_apl_file_content(self, file_id: str) -> dict[str, Any] | None:
        """获取APL文件内容。

        Args:
            file_id (str): APL文件标识。

        Returns:
            dict[str, Any] | None: 文件内容信息，未找到时返回None。
        """
        if not file_id or not isinstance(file_id, str):
            return None

        if file_id.startswith("default_"):
            rel_path = file_id[len("default_") :]
            base_dir = DEFAULT_APL_DIR
        elif file_id.startswith("custom_"):
            rel_path = file_id[len("custom_") :]
            base_dir = COSTOM_APL_DIR
        else:
            return None

        file_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"file_id": file_id, "content": content, "file_path": file_path}

    def create_apl_file(self, file_data: dict[str, Any]) -> str:
        """创建新的APL文件。

        Args:
            file_data (dict[str, Any]): APL文件数据。

        Returns:
            str: 新建APL文件的标识。

        Raises:
            Exception: 当写入文件失败时抛出。
        """
        if not file_data or not isinstance(file_data, dict):
            raise ValueError("文件数据不能为空且必须是字典类型")

        name = file_data.get("name", "new_apl.toml")
        content = file_data.get("content", "")
        if not name.endswith(".toml"):
            name += ".toml"
        file_path = os.path.join(COSTOM_APL_DIR, name)
        os.makedirs(COSTOM_APL_DIR, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return f"custom_{name}"

    def update_apl_file(self, file_id: str, content: str) -> bool:
        """更新APL文件内容。

        Args:
            file_id (str): APL文件标识。
            content (str): 文件内容。

        Returns:
            bool: 更新成功返回True，否则False。
        """
        if not file_id or not isinstance(file_id, str):
            return False
        if content is None or not isinstance(content, str):
            return False
        if file_id.startswith("default_"):
            return False
        if not file_id.startswith("custom_"):
            return False

        rel_path = file_id[len("custom_") :]
        file_path = os.path.join(COSTOM_APL_DIR, rel_path)
        if not os.path.exists(file_path):
            return False

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return True

    def delete_apl_file(self, file_id: str) -> bool:
        """删除APL文件。

        Args:
            file_id (str): APL文件标识。

        Returns:
            bool: 删除成功返回True，否则False。
        """
        if not file_id or not isinstance(file_id, str):
            return False
        if file_id.startswith("default_"):
            return False
        if not file_id.startswith("custom_"):
            return False

        rel_path = file_id[len("custom_") :]
        file_path = os.path.join(COSTOM_APL_DIR, rel_path)
        if not os.path.exists(file_path):
            return False

        os.remove(file_path)
        return True

    def _get_apl_from_dir(self, apl_dir: str, source_type: str) -> list[dict[str, Any]]:
        """从指定目录获取APL模板。

        Args:
            apl_dir (str): 目录路径。
            source_type (str): 模板来源标识。

        Returns:
            list[dict[str, Any]]: 模板列表。
        """

        apl_list: list[dict[str, Any]] = []
        if not os.path.exists(apl_dir):
            return apl_list
        for root, _, files in os.walk(apl_dir):
            for file_name in files:
                if not file_name.endswith(".toml"):
                    continue
                file_path = os.path.join(root, file_name)
                with open(file_path, "rb") as file:
                    apl_data = tomllib.load(file)
                general_info = apl_data.get("general", {})
                apl_list.append(
                    {
                        "id": f"{source_type}_{os.path.relpath(file_path, apl_dir).replace(os.sep, '_')}",
                        "title": general_info.get("title", ""),
                        "author": general_info.get("author", ""),
                        "comment": general_info.get("comment", ""),
                        "create_time": general_info.get("create_time", ""),
                        "latest_change_time": general_info.get("latest_change_time", ""),
                        "source": source_type,
                        "file_path": file_path,
                    }
                )
        return apl_list

    def _get_apl_files_from_dir(self, apl_dir: str, source_type: str) -> list[dict[str, Any]]:
        """从指定目录获取APL文件列表。

        Args:
            apl_dir (str): 目录路径。
            source_type (str): 模板来源标识。

        Returns:
            list[dict[str, Any]]: 文件信息列表。
        """

        file_list: list[dict[str, Any]] = []
        if not os.path.exists(apl_dir):
            return file_list
        for root, _, files in os.walk(apl_dir):
            for file_name in files:
                if not file_name.endswith(".toml"):
                    continue
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, apl_dir)
                file_list.append(
                    {
                        "id": f"{source_type}_{rel_path.replace(os.sep, '_')}",
                        "name": file_name,
                        "path": rel_path,
                        "source": source_type,
                        "full_path": file_path,
                    }
                )
        return file_list
