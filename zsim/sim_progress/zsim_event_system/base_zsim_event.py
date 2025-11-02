from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseZSimEventContext(BaseModel):
    """ZSim事件上下文,但通常不包含事件本身对应的复杂对象"""

    state_path: tuple[str, ...] = ()  # 事件处理的路径
    core_info: Dict[str, Any] = {}  # 事件处理的核心信息

    def with_state(self, node_id: str) -> "BaseZSimEventContext":
        """基于当前上下文创建一个新的上下文, 并在状态路径上添加新的节点ID"""
        return BaseZSimEventContext(
            state_path=self.state_path + (node_id,),
            core_info=self.core_info,
        )


class ZSimBaseEvent(ABC, BaseModel):
    """ZSim事件基类, 所有事件均应继承自此类"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))  # 事件唯一标识符
    context: BaseZSimEventContext = Field(default_factory=BaseZSimEventContext)  # 事件上下文信息
