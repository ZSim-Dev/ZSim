from typing import Iterable

from ....define import ZSimEventTypes
from ..zsim_events import EventMessage, SkillEventContext, ZSimEventABC
from .decorator import event_handler


@event_handler(ZSimEventTypes.SKILL_EVENT)
def skill_end_handler(event: ZSimEventABC[EventMessage], context: SkillEventContext
    ) -> Iterable[ZSimEventABC[EventMessage]]:

    return []
