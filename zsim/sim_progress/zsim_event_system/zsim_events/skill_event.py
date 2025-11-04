from ....define import SkillType
from ....define import ZSimEventTypes as ZET
from ...data_struct.single_hit import SingleHit
from ...Preload import SkillNode
from .base_zsim_event import ExecutionEvent
from .base_zsim_event import ZSimBaseEvent as ZBE


class SkillEvent(ZBE):
    """技能事件, 仅记录静态技能。在角色初始化时创建,被Character对象持有,在后续其他事件中被引用。"""

    @property
    def skill_type(self) -> SkillType:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.skill.skill_type


class SkillExecutionEvent(ExecutionEvent):
    """技能持续事件,构造时,封装一个SkillEvent的指针"""
    _is_active: bool = False  # 技能事件是否正式开始
    _hitted_count = 0  # 已经结算的技能命中计数
    _single_hit_avtive_timeline: dict[int, list[SingleHit]] = {}  # SingleHit激活时间线

    @property
    def skill_type(self) -> SkillType:
        assert isinstance(self.event_origin, SkillEvent)
        return self.event_origin.skill_type
