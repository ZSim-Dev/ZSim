# 这是席德围杀Buff的脚本

from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedBesiegeBonusRecord(BRBC):
    def __init__(self):
        super().__init__()


class SeedBesiegeBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是席德围杀Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xexit = self.special_exit_logic
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
            self.buff_0.history.record = SeedBesiegeBonusRecord()
        self.record = self.buff_0.history.record

    def special_exit_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        seed = self.record.char
        from zsim.sim_progress.Character.Seed import Seed

        assert isinstance(seed, Seed), (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        besiege_tuple = seed.besiege_active_check()
        beneficiary = kwargs.get("beneficiary", None)
        if beneficiary is None:
            print(
                f"【Buff退出警告】{self.buff_instance.ft.index} 的复杂逻辑模块未正确识别到输入参数“beneficiary”，遂终止Buff。请检查函数"
            )
            return True
        # 如果席德都没有指定正兵，那么肯定也不可能有围杀Buff
        if seed.vanguard is None:
            return True
        if beneficiary == "席德":
            return not besiege_tuple[0]
        elif beneficiary == seed.vanguard.NAME:
            return not besiege_tuple[1]
        else:
            # 别的角色不可能保留围杀Buff
            return True
