from ..Preload import SkillNode
from .base_zsim_event import ZSimBaseEvent as ZBE
from ...define import ZSimEventTypes as ZET
from dataclasses import dataclass


@dataclass
class SkillEvent(ZBE):
    """技能开始事件, 用于表示一个技能的启动"""

    def __init__(self, event_context):
        super().__init__(event_type=ZET.SKILL_EVENT, event_context=event_context)
        assert hasattr(self.event_context, "skill_node"), (
            f"传入的上下文并未包含{self.event_type}类事件所必需的skill_node属性"
        )
