from abc import ABC, abstractmethod
from typing import Generic, Iterable, TypeVar

from ..zsim_events import BaseZSimEventContext, EventMessage, ZSimEventABC

T = TypeVar("T", bound=EventMessage)


class ZSimEventHandler(Generic[T], ABC):
    @abstractmethod
    def supports(self, event: ZSimEventABC[T]) -> bool:
        """检查该处理器是否支持处理给定的事件"""
        ...

    @abstractmethod
    def handle(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[ZSimEventABC[EventMessage]]:
        """处理给定的事件, 并可能产生新的事件"""
        ...
