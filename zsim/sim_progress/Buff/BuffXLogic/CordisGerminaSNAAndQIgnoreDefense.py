from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as Brbc


class CordisGerminaSNAAndQIgnoreDefenseRecord(Brbc):
    def __init__(self):
        super().__init__()


class CordisGerminaSNAAndQIgnoreDefense(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是机巧心种普攻大招无视防御Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.xexit = self.special_exit_logic
        self.equipper = None
        self.buff_0 = None
        self.record: CordisGerminaSNAAndQIgnoreDefenseRecord | None = None

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
            self.buff_0.history.record = CordisGerminaSNAAndQIgnoreDefenseRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(equipper="机巧心种", trigger_buff_0=("equipper", "机巧心种-电属性增伤"))
        assert self.record is not None
        assert self.record.trigger_buff_0 is not None
        result = len(self.record.trigger_buff_0.dy.built_in_buff_box) == 2
        return result

    def special_exit_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(equipper="机巧心种", trigger_buff_0=("equipper", "机巧心种-电属性增伤"))
        return not self.xjudge


