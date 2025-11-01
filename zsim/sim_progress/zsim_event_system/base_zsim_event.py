from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field

from ..Buff.buff_class import Buff
from ..Character.character import Character
from ..Preload.SkillsQueue import SkillNode


class BaseZSimEventContext(BaseModel):
    """ZSim事件上下文, 用于记录事件处理过程中的路径和信息变化"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))  # 事件唯一标识符
    state_path: tuple[str, ...] = ()  # 事件处理的路径
    core_info: Dict[str, Any] = {}  # 事件处理的核心信息

    def with_state(self, node_id: str) -> "BaseZSimEventContext":
        """基于当前上下文创建一个新的上下文, 并在状态路径上添加新的节点ID"""
        return BaseZSimEventContext(
            state_path=self.state_path + (node_id,),
            core_info=self.core_info,
        )


class CharacterEventContext(BaseZSimEventContext):
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


class SkillEventContext(BaseZSimEventContext):
    """技能事件信息载荷"""

    skill_node: SkillNode

    @property
    def skill_tag(self) -> str:
        """获取技能标签"""
        return self.skill_node.skill_tag

    @property
    def trigger_buff_level(self) -> int:
        """获取技能的触发类型"""
        return self.skill_node.skill.trigger_buff_level

class BuffEventContext(BaseZSimEventContext):
    """Buff事件信息载荷"""

    buff: Buff

    @property
    def buff_index(self) -> str:
        """获取技能标签"""
        return self.buff.ft.index

