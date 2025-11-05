from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Protocol, TypeVar

from ....define import ZSimEventTypes
from ..zsim_events import BaseZSimEventContext, ZSimEventABC

T = TypeVar("T", bound=BaseZSimEventContext)


class EventConditionFn(Protocol):
    """事件条件判断协议"""

    def __call__(self, event: ZSimEventABC[T]) -> bool: ...


class EventCondition(ABC):
    @abstractmethod
    def evaluate(self, event: ZSimEventABC[T]) -> bool: ...


@dataclass
class EventTransition:
    """节点中转,指向另一个节点或者多个子节点"""

    condition: EventCondition
    target: "EventTreeNode"

    def matches(self, event: ZSimEventABC[T]) -> bool:
        return self.condition.evaluate(event)


class EventTreeNode(ABC):
    """事件状态数节点基类"""

    def __init__(self, node_id: str):
        self.node_id = node_id

    @abstractmethod
    def _handle(self, event: ZSimEventABC[T]) -> Iterable[ZSimEventABC[BaseZSimEventContext]]: ...

    def handle(self, event: ZSimEventABC[T]) -> Iterable[ZSimEventABC[BaseZSimEventContext]]:
        context = event.event_context
        context.append_state_node(self.node_id)
        yield from self._handle(event=event)


class EventBranchNode(EventTreeNode):
    """分支节点,不承担具体的业务,只负责路由"""

    def __init__(self, node_id: str):
        super().__init__(node_id=node_id)
        self._transitions: dict[ZSimEventTypes, list[EventTransition]] = {}

    def add_transition(self, listen_event: ZSimEventTypes, transition: EventTransition) -> None:
        """"""
        self._transitions.setdefault(listen_event, []).append(transition)

    def _handle(self, event: ZSimEventABC[T]) -> Iterable[ZSimEventABC[BaseZSimEventContext]]:
        """"""
        transitions = self._transitions.get(event.event_type, [])
        for transition in transitions:
            if transition.matches(event=event):
                yield from transition.target.handle(event=event)
