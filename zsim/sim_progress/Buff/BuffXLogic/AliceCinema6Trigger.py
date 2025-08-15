from .. import Buff, JudgeTools, check_preparation
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.sim_progress.Character.Alice import Alice


class AliceCinema6TriggerRecord:
    def __init__(self):
        self.char: "Alice | None" = None


class AliceCinema6Trigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.xhit = self.special_hit_logic
        self.buff_0 = None
        self.record: AliceCinema6TriggerRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["爱丽丝"][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = AliceCinema6TriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """爱丽丝的6画额外攻击逻辑判定函数，只会在决胜状态可用时放行队友技能的命中事件"""
        self.check_record_module()
        self.get_prepared(char_CID=1401)
        skill_node = kwargs.get("skill_node")
        if skill_node is None:
            return False
        skill_node: "SkillNode"

        # 首先过滤掉自己的技能
        if skill_node.char_name == self.record.char.NAME:
            return False

        # 当爱丽丝不处于决胜状态时，不触发
        if not self.record.char.victory_state:
            return False

        # 过滤掉并非处于命中帧的技能
        if not skill_node.is_hit_now(tick=self.buff_instance.sim_instance.tick):
            return False
        else:
            return True

    def special_hit_logic(self, **kwargs):
        """爱丽丝6画额外攻击触发器的业务函数，主要负责抛出额外攻击"""
        self.check_record_module()
        self.get_prepared(char_CID=1401)



