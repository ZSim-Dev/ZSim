from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as Brbc


class DawnsBloom4SetTriggerNADmgBonusRecord(Brbc):
    def __init__(self):
        super().__init__()


class DawnsBloom4SetTriggerNADmgBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是拂晓生花四件套触发普攻增伤Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.equipper = None
        self.buff_0 = None
        self.record: DawnsBloom4SetTriggerNADmgBonusRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.equipper is None:
            self.equipper = JudgeTools.find_equipper(
                "拂晓生花", sim_instance=self.buff_instance.sim_instance
            )
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )[self.equipper][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = DawnsBloom4SetTriggerNADmgBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """拂晓生花4件套触发普攻增伤，仅对强攻角色生效"""
        self.check_record_module()
        self.get_prepared(equipper="拂晓生花")
        assert self.record is not None
        # 对于非强攻角色，永远不触发
        if self.record.char.specialty != "强攻":
            return False
        skill_node = kwargs.get("skill_node", None)
        if skill_node is None:
            return False
        from zsim.sim_progress.Preload import SkillNode
        assert isinstance(skill_node, SkillNode)
        # 筛选掉不是强化E和大招的技能
        if skill_node.skill.trigger_buff_level not in [2, 6]:
            return False
        tick = self.buff_instance.sim_instance.tick
        if skill_node.preload_tick != tick:
            return False
        else:
            return True
