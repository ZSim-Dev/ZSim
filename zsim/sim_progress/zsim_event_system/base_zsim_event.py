from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field

from ..Buff.buff_class import Buff
from ..Character.character import Character
from ..Preload.SkillsQueue import SkillNode


class BaseZSimEventMessage(BaseModel):
    """ZSim事件信息载荷(基类), 信息载荷承担着上下文作用, 通常直接包含复杂对象"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))  # 事件唯一标识符


class BaseZSimEventContext(BaseModel):
    """ZSim事件上下文, 用于记录事件处理过程中的路径和信息变化"""

    state_path: tuple[str, ...] = ()  # 事件处理的路径
    core_info: Dict[str, Any] = {}  # 事件处理的核心信息

    def with_state(self, node_id: str) -> "BaseZSimEventContext":
        """基于当前上下文创建一个新的上下文, 并在状态路径上添加新的节点ID"""
        return BaseZSimEventContext(
            state_path=self.state_path + (node_id,),
            core_info=self.core_info,
        )


class CharacterEventMessage(BaseZSimEventMessage):
    """角色事件信息载荷"""

    character: Character  # 角色对象

    @property
    def character_name(self) -> str:
        """获取角色名称"""
        return self.character.NAME

    @property
    def character_cid(self) -> int:
        """获取角色CID"""
        return self.character.CID


class SkillEventMessage(BaseZSimEventMessage):
    """技能事件信息载荷"""

    skill_node: SkillNode

    @property
    def skill_tag(self) -> str:
        """获取技能标签"""
        return self.skill_node.skill_tag


class BuffEventMessage(BaseZSimEventMessage):
    """Buff事件信息载荷"""

    buff: Buff

    @property
    def buff_index(self) -> str:
        """获取技能标签"""
        return self.buff.ft.index
