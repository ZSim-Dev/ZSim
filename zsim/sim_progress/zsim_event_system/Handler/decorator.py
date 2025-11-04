from functools import wraps
from typing import Any, Callable, Iterable, TypeVar, cast

from ....define import ZSimEventTypes
from ..zsim_events import (
    BaseZSimEventContext,
    ZSimEventABC,
)
from .base_handler_class import ZSimEventHandler
from .zsim_event_handler_registry import ZSimEventHandlerRegistry

# 全局的注册表实例
_global_hander_registry: ZSimEventHandlerRegistry | None = None

HandlerFunc = Callable[..., Iterable[ZSimEventABC[BaseZSimEventContext]]]
F = TypeVar("F", bound=HandlerFunc)
HandlerType = TypeVar("HandlerType", bound=ZSimEventHandler[Any])


def get_global_handler_registry() -> ZSimEventHandlerRegistry:
    """获取全局的事件处理器注册表实例"""
    global _global_hander_registry
    if _global_hander_registry is None:
        _global_hander_registry = ZSimEventHandlerRegistry()
    return _global_hander_registry


def event_handler(event_type: ZSimEventTypes) -> Callable[[F], F]:
    """
    事件处理装饰器, 用于自动注册Handler到全局注册表

    Args:
        event_type (ZSimEventTypes): 事件类型

    Returns:
        装饰器函数对象

    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(event: ZSimEventABC[Any]) -> Iterable[ZSimEventABC[BaseZSimEventContext]]:
            return func(event)

        class FunctionEventHandler(ZSimEventHandler[BaseZSimEventContext]):
            def __init__(self, handler_func: HandlerFunc):
                self._handler_func = handler_func
                self._event_type = event_type

            def supports(self, event: ZSimEventABC[BaseZSimEventContext]) -> bool:
                return event.event_type == self._event_type

            def handle(
                self, event: ZSimEventABC[BaseZSimEventContext]
            ) -> list[ZSimEventABC[BaseZSimEventContext]]:
                return list(self._handler_func(event))

            def __repr__(self) -> str:
                return f"构造了FunctionEventHandler对象, 参数为：(event_type={self._event_type}, handler_func={self._handler_func.__name__})"

        registry = get_global_handler_registry()
        handler_instance: ZSimEventHandler[BaseZSimEventContext] = FunctionEventHandler(func)
        registry.register(event_type, handler_instance)

        # 将处理器实例(FunctionEventHandler)和事件类型附加到包装函数上
        setattr(wrapper, "_event_handler", handler_instance)  # noqa: B010
        setattr(wrapper, "_event_type", event_type)  # noqa: B010

        return cast(F, wrapper)

    return decorator


"""注意,考虑到业务尚未拓展,暂时不提供另外的注册接口,仅实现event_handler这一个装饰器。"""


def clear_registry() -> None:
    """清空全局事件处理器注册表"""
    global _global_hander_registry
    _global_hander_registry = None
