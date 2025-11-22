from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as Brbc


class CordisGerminaEleDmgBonusRecord(Brbc):
    def __init__(self):
        super().__init__()


class CordisGerminaEleDmgBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是机巧心种电属性增伤Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.equipper = None
        self.buff_0 = None
        self.record: CordisGerminaEleDmgBonusRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.equipper is None:
            self.equipper = JudgeTools.find_equipper(
                "机巧心种", sim_instance=self.buff_instance.sim_instance
            )
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )[self.equipper][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = CordisGerminaEleDmgBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """机巧心种的电属性增伤Buff触发器，由于在后台也需要监听，所以这里需要用脚本进行判断"""
        self.check_record_module()
        self.get_prepared(equipper="机巧心种")
        assert self.record is not None
        skill_node = kwargs.get("skill_node", None)
        from zsim.sim_progress.Preload import SkillNode

        assert isinstance(skill_node, SkillNode)
        # 首先筛选掉没有佩戴机巧心种的角色的技能
        if skill_node.char_name != self.record.char.NAME:
            return False
        # 筛选掉不是强化E和普攻的技能。
        if skill_node.skill.trigger_buff_level not in [0, 2]:
            return False
        # 筛选掉非命中帧
        tick = self.buff_instance.sim_instance.tick
        if not skill_node.is_hit_now(tick=tick):
            return False
        else:
            return True
