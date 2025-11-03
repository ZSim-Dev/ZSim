from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field

from ...define import ZSimEventTypes


class BaseZSimEventContext(BaseModel):
    """ZSim事件上下文,但通常不包含事件本身对应的复杂对象"""

    state_path: tuple[str, ...] = ()  # 事件处理的路径
    core_info: Dict[str, Any] = {}  # 事件处理的核心信息

    def append_state_node(
        self,
        node_id: str,
    ) -> None:
        """为事件上下文添加状态路径, 作为事件处理的最后一步"""
        self.state_path += (node_id,)


class ZSimEventABC[T: BaseZSimEventContext](ABC):
    """ZSim事件接口, 所有事件均应实现此接口"""

    @property
    @abstractmethod
    def event_type(self) -> ZSimEventTypes: ...

    @property
    @abstractmethod
    def event_context(self) -> T: ...


class ZSimBaseEvent[T: BaseZSimEventContext](ZSimEventABC[T]):
    """ZSim事件基类, 所有事件均应继承自此类"""

    def __init__(self, event_type: ZSimEventTypes, event_context: T) -> None:
        self._event_type = event_type
        self._event_context: T = event_context

    @property
    def event_type(self) -> ZSimEventTypes:
        return self._event_type

    @property
    def event_context(self) -> BaseZSimEventContext:
        return self._event_context
