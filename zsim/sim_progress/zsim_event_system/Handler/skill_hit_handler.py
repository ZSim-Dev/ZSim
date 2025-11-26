from typing import Iterable, TypeVar

from ....define import ZSimEventTypes
from ..zsim_events import EventMessage, SkillEventContext, SkillExecutionEvent, ZSimEventABC
from .decorator import event_handler

T = TypeVar("T", bound=EventMessage)


@event_handler(ZSimEventTypes.SKILL_EVENT)
def skill_hit_handler(
    event: ZSimEventABC[EventMessage], context: SkillEventContext
) -> Iterable[ZSimEventABC[EventMessage]]:
    """处理技能命中事件的Handler

    Args:
        event (ZSimEventABC[EventMessage]): 技能事件
        context (SkillEventContext): 技能事件上下文

    Returns:
        不产生新事件
    """
    assert isinstance(event, SkillExecutionEvent)

    return []
