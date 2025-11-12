from typing import TypeVar

from ..zsim_events import BaseZSimEventContext, EventMessage, ZSimEventABC
from .nodes import EventTreeNode

T = TypeVar("T", bound=EventMessage)


class EventStateTree:
    """事件状态树, 负责分发事件并路由到对应节点"""

    def __init__(self, root: EventTreeNode):
        self._root = root

    @property
    def root(self) -> EventTreeNode:
        return self._root

    def dispatch(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> list[tuple[ZSimEventABC[EventMessage], BaseZSimEventContext]]:
        """
        分发事件,将接收到的事件路由到对应节点,并返回所有产生的事件
        """
        return list(self._root.handle(event=event, context=context))
