from ..Preload import SkillNode
from .base_zsim_event import ZSimBaseEvent as ZBE


class SkillStartEvent(ZBE):
    """技能开始事件, 用于表示一个技能的启动"""

    skill_node: SkillNode




class SkillHitEvent(ZBE):
    """技能命中事件, 用于表示一个技能的命中"""

    skill_node: SkillNode



class SkillEndEvent(ZBE):
    """技能结束事件, 用于表示一个技能的结束"""

    skill_node: SkillNode




class SkillInteruppedEvent(ZBE):
    """技能被打断事件, 用于表示一个技能的被打断"""

    skill_node: SkillNode

