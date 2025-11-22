# 这是席德围杀Buff的脚本

from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedBesiegeBonusTriggerRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.buff_index = "Buff-角色-席德-围杀"


class SeedBesiegeBonusTrigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是席德围杀Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.xhit = self.special_hit_logic
        self.buff_0: "Buff | None" = None
        self.record: BRBC | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["席德"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, (
            "【Buff初始化警告】席德的复杂逻辑模块未正确初始化，请检查函数"
        )
        if self.buff_0.history.record is None:
            self.buff_0.history.record = SeedBesiegeBonusTriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        from zsim.sim_progress.Character.Seed import Seed

        seed = self.record.char
        assert isinstance(seed, Seed)
        besiege_state_tuple = seed.besiege_active_check()
        if any(besiege_state_tuple):
            return True
        else:
            return False

    def special_hit_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None
        from zsim.sim_progress.Character.Seed import Seed

        seed = self.record.char
        assert isinstance(seed, Seed)
        besiege_state_tuple = seed.besiege_active_check()
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy

        benefit_list = []
        if besiege_state_tuple[0]:
            benefit_list.append("席德")
        if besiege_state_tuple[1]:
            benefit_list.append(seed.vanguard.NAME) if seed.vanguard is not None else None
        if benefit_list:
            buff_add_strategy(
                self.record.buff_index,
                benifit_list=benefit_list,
                sim_instance=self.buff_instance.sim_instance,
            )
