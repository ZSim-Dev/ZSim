from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedOnslaughtBonusRecord(BRBC):
    def __init__(self):
        super().__init__()


class SeedOnslaughtBonus(Buff.BuffLogic):
    """席德的强袭Buff复杂逻辑"""
    def __init__(self, buff_instance):
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
            self.buff_0.history.record = SeedOnslaughtBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """席德的强袭状态早就已经记录在席德的特殊资源中了，所以这里不需要重复判断，只需要直接调用方法判断是否生效即可"""
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        from zsim.sim_progress.Character.Seed import Seed
        assert isinstance(self.record.char, Seed), False

        return self.record.char.onslaught_active

    def special_exit_logic(self, **kwargs):
        """强袭Buff的退出逻辑和生效逻辑相反，所以这里需要调用席德的方法退出强袭状态"""
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        return not self.xjudge

