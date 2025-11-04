from collections import defaultdict
from typing import Any, DefaultDict, Generator, Iterable, TypeVar

from ....define import ZSimEventTypes
from ..zsim_events import BaseZSimEventContext, ZSimEventABC
from .base_handler_class import ZSimEventHandler

T = TypeVar("T", bound=BaseZSimEventContext)


class ZSimEventHandlerRegistry:
    """事件Handler注册表, 用于管理和检索事件Handler类"""

    def __init__(self):
        self._handlers: DefaultDict[ZSimEventTypes, list[ZSimEventHandler[Any]]] = defaultdict(list)

    def register(self, event_type: ZSimEventTypes, handler: ZSimEventHandler[Any]) -> None:
        """注册事件处理器类到指定事件类型"""
        self._handlers[event_type].append(handler)

    def iter_handlers(self, event: ZSimEventABC[T]) -> Iterable[ZSimEventHandler[Any]]:
        """迭代所有支持处理给定事件的处理器"""
        for handler in self._handlers.get(event.event_type, []):
            if handler.supports(event):
                yield handler

    def handle(self, event: ZSimEventABC[T]) -> Generator[ZSimEventABC[BaseZSimEventContext]]:
        """处理给定的事件, 并可能产生新的事件"""
        for handler in self.iter_handlers(event):
            yield from handler.handle(event)
