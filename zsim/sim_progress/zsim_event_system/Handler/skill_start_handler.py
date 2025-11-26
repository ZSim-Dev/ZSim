from typing import TYPE_CHECKING, Iterable, TypeVar

from ....define import SkillSubEventTypes, ZSimEventTypes
from ..zsim_events import EventMessage, ZSimEventABC
from ..zsim_events.skill_event import (
    SkillEvent,
    SkillEventContext,
    SkillEventMessage,
    SkillExecutionEvent,
)
from .decorator import event_handler

if TYPE_CHECKING:
    from ...Preload import SkillNode

T = TypeVar("T", bound=EventMessage)


@event_handler(ZSimEventTypes.SKILL_EVENT)
def skill_start_handler(
    event: ZSimEventABC[EventMessage], context: SkillEventContext
) -> Iterable[SkillExecutionEvent]:
    """
    技能开始事件Handler,该Handler接收一个SkillEvent事件,返回一个ExecutionEvent 事件
    """
    assert isinstance(event, SkillEvent), (

        f"skill_start_handler接收的event类型只能是SkillEvent,当前event类型为{type(event).__name__}"

    )
    assert isinstance(event.event_origin, SkillNode)
    assert context.preload_tick is not None, "preload_tick不能为None"
    event_message = SkillEventMessage(skill_tag=event.event_origin.skill_tag)
    event_message.preload_tick = context.preload_tick
    skill_execution_event = SkillExecutionEvent(
        event_type=SkillSubEventTypes.START,
        event_origin=event,  # type: ignore
        event_message=event_message,
    )
    # 调用execution_event内置的开始方法,计算整体命中时间
    skill_execution_event.skill_event_start()

    print(f"【ZSim新架构调试】技能开始事件Handler处理技能{event.event_origin.skill_tag}开始执行")
    return [skill_execution_event]
