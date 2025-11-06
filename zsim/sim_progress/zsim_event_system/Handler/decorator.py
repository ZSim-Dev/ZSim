from functools import wraps
from typing import Any, Callable, Iterable, Protocol, TypeVar, cast

from ....define import ZSimEventTypes
from ..zsim_events import BaseZSimEventContext, EventMessage, ZSimEventABC
from .base_handler_class import ZSimEventHandler
from .zsim_event_handler_registry import ZSimEventHandlerRegistry

# 全局的注册表实例
_global_hander_registry: ZSimEventHandlerRegistry | None = None
T = TypeVar("T", bound=EventMessage)
C = TypeVar("C", bound=BaseZSimEventContext, contravariant=True)
"""
笔记：
原有方案中,我们指定了HandlerFunc接收一个抽象基类BaseZSimEventContext,
但实际上,各个handler传入的是更加具体的类型,比如SkillEventContext或者其他。
这些更具体的Context都是从BaseZSimEventContext继承而来的,是它的子类，
所以,在接收这些Context的HandlerFunc中,这种子类关系会被转化为一种逆变关系：
即：
SkillEventContext <: BaseZSimEventContext
HandlerFunc[BaseZSimEventContext] <: HandlerFunc[SkillEventContext]
解释转译：
HandlerFunc[BaseZSimEventContext]宣称能够处理所有类型的Context,自然也能处理SkillEventContext类型,
但HandlerFunc[SkillEventContext]并不一定能处理BaseZSimEventContext类型,
从这个角度来看,功能更全面的那个应该是子类,功能更狭隘的那个应该是父类
所以, HandlerFunc[SkillEventContext]是父类,HandlerFunc[BaseZSimEventContext]是子类。

因此,我们需要修改HandlerFunc的类型定义,让contravariant参数为True,
"""


class HandlerFunc(Protocol[C]):
    """事件处理函数协议"""

    def __call__(
        self, event: ZSimEventABC[T], context: C
    ) -> Iterable[ZSimEventABC[EventMessage]]: ...

    __name__: str


F = TypeVar("F", bound=HandlerFunc[Any])


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
        def wrapper(
            event: ZSimEventABC[T], context: BaseZSimEventContext
        ) -> Iterable[ZSimEventABC[EventMessage]]:
            return func(event, context)

        class FunctionEventHandler(ZSimEventHandler[EventMessage]):
            def __init__(self, handler_func: F):
                self._handler_func = handler_func
                self._event_type = event_type

            def supports(self, event: ZSimEventABC[T]) -> bool:
                return event.event_type == self._event_type

            def handle(
                self, event: ZSimEventABC[T], context: BaseZSimEventContext
            ) -> list[ZSimEventABC[EventMessage]]:
                return list(self._handler_func(event, context))

            def __repr__(self) -> str:
                return f"构造了FunctionEventHandler对象, 参数为：(event_type={self._event_type}, handler_func={self._handler_func.__name__})"

        registry = get_global_handler_registry()
        handler_instance: ZSimEventHandler[EventMessage] = FunctionEventHandler(func)
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
