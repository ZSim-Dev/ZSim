from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from typing import Any, Callable, Iterable, Protocol, Sequence, TypeVar, cast

from ....define import SkillSubEventTypes, ZSimEventTypes
from ..zsim_events import BaseZSimEventContext, EventMessage, ZSimEventABC

T = TypeVar("T", bound=EventMessage)
T_contra = TypeVar("T_contra", bound=EventMessage, contravariant=True)


class EventConditionFn(Protocol):
    """事件条件判断协议"""
    def __call__(self, event: ZSimEventABC[T], context: BaseZSimEventContext) -> bool: ...


class EventActionFn(Protocol[T_contra]):
    """事件操作函数协议"""

    def __call__(
        self, event: ZSimEventABC[T_contra], context: BaseZSimEventContext
    ) -> Iterable[ZSimEventABC[EventMessage]]: ...



class EventCondition(ABC):
    """事件条件判断基类"""

    @abstractmethod
    def evaluate(self, event: ZSimEventABC[T], context: BaseZSimEventContext) -> bool: ...


class EventAction(ABC):
    """当节点的条件被满足时, 会执行的操作"""

    @abstractmethod
    def produce(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[ZSimEventABC[EventMessage]]: ...


@dataclass(frozen=True)
class LeafConfiguration:
    """描述动态叶子运行方式的配置"""


    listen_event: ZSimEventTypes | SkillSubEventTypes  # 监听的事件类型

    condition: EventCondition  # 事件条件判断
    actions: Sequence[EventAction] = field(default_factory=tuple)  # 事件满足条件时,执行的操作


class EventConfigRepository(Protocol):
    """加载事件配置的仓库协议"""

    def load_leaf_config(self, node_id: str) -> Sequence[LeafConfiguration]: ...


@dataclass
class EventTransition:
    """节点中转,指向另一个节点或者多个子节点"""

    condition: EventCondition
    target: "EventTreeNode"

    def matches(self, event: ZSimEventABC[T], context: BaseZSimEventContext) -> bool:
        return self.condition.evaluate(event, context)


class EventTreeNode(ABC):
    """事件状态数节点基类"""

    def __init__(self, node_id: str):
        self.node_id = node_id

    @abstractmethod
    def _handle(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[tuple[ZSimEventABC[EventMessage], BaseZSimEventContext]]: ...

    def handle(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[tuple[ZSimEventABC[EventMessage], BaseZSimEventContext]]:
        """新增一个节点"""
        context.append_state_node(self.node_id)
        yield from self._handle(event=event, context=context)


class EventBranchNode(EventTreeNode):
    """分支节点,不承担具体的业务,只负责路由"""

    def __init__(self, node_id: str):
        super().__init__(node_id=node_id)

        self._transitions: dict[ZSimEventTypes | SkillSubEventTypes, list[EventTransition]] = {}

    def add_transition(
        self, listen_event: ZSimEventTypes | SkillSubEventTypes, transition: EventTransition
    ) -> None:

        """添加一个事件转换"""
        self._transitions.setdefault(listen_event, []).append(transition)

    def _handle(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[tuple[ZSimEventABC[EventMessage], BaseZSimEventContext]]:
        """处理事件,将事件路由到对应目标节点"""
        transitions = self._transitions.get(event.event_type, [])
        for transition in transitions:
            if transition.matches(event=event, context=context):
                yield from transition.target.handle(event=event, context=context)


class DynamicLeafNode(EventTreeNode):
    """动态叶子节点,承担具体的业务"""

    def __init__(self, node_id: str, repository: EventConfigRepository):
        super().__init__(node_id)
        self._repository = repository
        self._config: Sequence[LeafConfiguration] | None = None

    def _ensure_config_loaded(self) -> Sequence[LeafConfiguration]:
        """确保配置已经被正确加载"""
        if self._config is None:
            self._config = self._repository.load_leaf_config(self.node_id)
        return self._config

    def _handle(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[tuple[ZSimEventABC[EventMessage], BaseZSimEventContext]]:
        """处理事件,根据配置判断是否执行操作"""
        configs = self._ensure_config_loaded()
        for config in configs:
            if config.listen_event != event.event_type:
                # 不是监听的事件类型, 跳过
                continue
            if not config.condition.evaluate(event=event, context=context):
                # 事件条件不满足, 跳过
                continue
            # 事件条件满足, 执行操作
            for action in config.actions:
                # 执行操作, 并将产生的事件返回
                for produced in action.produce(event=event, context=context):
                    yield produced, context


class CallableCondition(EventCondition):
    """包装基本的函数判断器对象"""

    def __init__(self, fn: EventConditionFn):
        self._fn = fn

    def evaluate(self, event: ZSimEventABC[T], context: BaseZSimEventContext) -> bool:
        return bool(self._fn(event, context))


class CallableAction(EventAction):
    """包装函数触发器"""

    def __init__(self, fn: Callable[..., Any]):
        self._fn = fn

    def produce(
        self, event: ZSimEventABC[T], context: BaseZSimEventContext
    ) -> Iterable[ZSimEventABC[EventMessage]]:
        fn = cast(
            Callable[
                [ZSimEventABC[EventMessage], BaseZSimEventContext],
                Iterable[ZSimEventABC[EventMessage]],
            ],
            self._fn,
        )
        return list(fn(event, context))

