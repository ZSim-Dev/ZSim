from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class OrphieAdditionalAbilityIgnoreDefenseRecord(BRBC):
    def __init__(self):
        super().__init__()


class OrphieAdditionalAbilityIgnoreDefense(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是奥菲斯额外能力准星聚焦无视防御力Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.buff_0: "Buff | None" = None
        self.record: BRBC | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["奥菲斯"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, (
            "【Buff初始化警告】奥菲斯的复杂逻辑模块未正确初始化，请检查函数"
        )
        if self.buff_0.history.record is None:
            self.buff_0.history.record = OrphieAdditionalAbilityIgnoreDefenseRecord()
        self.record = self.buff_0.history.record
