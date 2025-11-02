from collections import defaultdict
from typing import Any, DefaultDict, Generator, Iterable, TypeVar

from define import BuffEventTypes, SkillEventTypes, ZSimEventTypes

from .base_handler_class import ZSimEventHandler

_global_event_handler_registry = {}


class EventHandlerRegistry:
    """事件处理器注册表, 用于管理和检索事件处理器类"""
    def __init__(self):
        self._handlers: DefaultDict[ZSimEventTypes | BuffEventTypes | SkillEventTypes, list[ZSimEventHandler[Any]]] = defaultdict(list)

    def register(self, event_type: ZSimEventTypes | BuffEventTypes | SkillEventTypes, handler: ZSimEventHandler[Any]) -> None:
        """注册事件处理器类到指定事件类型"""
        self._handlers[event_type].append(handler)

