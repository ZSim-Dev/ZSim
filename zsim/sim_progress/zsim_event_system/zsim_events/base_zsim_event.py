from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import uuid4

from pydantic import BaseModel, Field


from ....define import SkillSubEventTypes, ZSimEventTypes


if TYPE_CHECKING:
    from ...anomaly_bar import AnomalyBar
    from ...Buff import Buff
    from ...Character import Character
    from ...Preload import SkillNode

    from .skill_event import SkillEvent, SkillEventMessage



class EventMessage(BaseModel):
    """事件信息基类,用于记录事件的基本信息(一经设定不可更改)"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))


T = TypeVar("T", bound=EventMessage)

EventOriginType = Union[
    "SkillNode", "Buff", "AnomalyBar", "Character", "SkillEvent[SkillEventMessage]", None
]


class BaseZSimEventContext(BaseModel):
    """ZSim事件上下文,但通常不包含事件本身对应的复杂对象"""

    state_path: tuple[str, ...] = ()  # 事件处理的路径
    core_info: dict[str, Any] = {}  # 事件处理的核心信息

    def append_state_node(self, node_id: str) -> None:
        """为事件上下文添加状态路径, 作为事件处理的最后一步"""
        self.state_path += (node_id,)


class ZSimEventABC[T: EventMessage](ABC):
    """ZSim事件接口, 所有事件均应实现此接口"""

    @property
    @abstractmethod
    def event_type(self) -> ZSimEventTypes | SkillSubEventTypes: ...
      
    @property
    @abstractmethod
    def event_message(self) -> T: ...


class ZSimBaseEvent[T: EventMessage](ZSimEventABC[T]):
    """ZSim事件基类, 所有事件均应继承自此类"""

    def __init__(
        self,
        event_type: ZSimEventTypes | SkillSubEventTypes,
        event_message: T,
        event_origin: EventOriginType,
    ) -> None:
        self._event_type = event_type
        self._event_message: T = event_message
        self._event_origin: EventOriginType = event_origin  # 构造事件的源头复杂对象

    @property
    def event_type(self) -> ZSimEventTypes | SkillSubEventTypes:

        return self._event_type

    @property
    def event_message(self) -> T:
        return self._event_message

    @property
    def event_origin(self) -> EventOriginType:
        return self._event_origin


class ExecutionEvent(ZSimBaseEvent[EventMessage]):
    """动态事件,表示一段时间内持续存在的事件,具有多时间点执行的特性"""

    pass
