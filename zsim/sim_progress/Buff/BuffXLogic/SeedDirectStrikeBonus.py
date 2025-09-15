# 这是席德明攻Buff的脚本
from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedDirectStrikeBonusRecord(BRBC):
    def __init__(self):
        super().__init__()


class SeedDirectStrikeBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是席德明攻Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
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
            self.buff_0.history.record = SeedDirectStrikeBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """判断席德的明攻Buff生效情况"""
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        from zsim.sim_progress.Character.Seed import Seed
        seed: Seed = self.record.char
        if seed.vanguard is None:
            # 当席德的没有队友被指定为“正兵”时，明攻永远不可能触发。
            return False
        benifiter_name = self.buff_instance.ft.beneficiary
        name_box = ["席德"] + [seed.vanguard.NAME]

        # 当 当前Buff的收益人不属于席德或正兵时，直接返回False
        if benifiter_name not in name_box:
            return False

        # 直接运行席德的围攻状态判断函数
        return seed.direct_strike_active

    def special_exit_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        return not self.xjudge

