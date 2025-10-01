from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class OrphieCinema1DmgBonusRecord(BRBC):
    def __init__(self):
        super().__init__()


class OrphieCinema1DmgBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是奥菲斯影画1画准星聚焦增伤Buff的脚本，本Buff的触发行为完全由外部结构控制，自身只具有退出逻辑，结构类似于组队被动减防。"""
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
            )["奥菲斯"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, (
            "【Buff初始化警告】奥菲斯的复杂逻辑模块未正确初始化，请检查函数"
        )
        if self.buff_0.history.record is None:
            self.buff_0.history.record = OrphieCinema1DmgBonusRecord()
        self.record = self.buff_0.history.record

    def special_exit_logic(self, **kwargs):
        """调用奥菲斯的准星聚焦管理器来判断准星聚焦是否结束。"""
        self.check_record_module()
        self.get_prepared(CID=1301)
        beneficiary = kwargs.get("beneficiary")
        assert self.record is not None
        from zsim.sim_progress.Character.Orphie import Orphie

        assert isinstance(self.record.char, Orphie)
        state_dict: dict[int, bool] = self.record.char.zeroed_state_manager.get_zeroed_state_group()
        sim_instance = self.buff_instance.sim_instance
        assert sim_instance is not None
        beneficiary_obj = sim_instance.char_data.find_char_obj(char_name=beneficiary)
        if beneficiary_obj is None:
            raise ValueError(
                f"【奥菲斯事件警告】{self.buff_instance.ft.index} 的退出函数中，找不到角色 {beneficiary} 的角色实例"
            )
        if beneficiary_obj.CID not in state_dict:
            raise ValueError(
                f"【奥菲斯事件警告】{self.buff_instance.ft.index} 的退出函数中，找不到CID为 {beneficiary_obj.CID} 的准星聚焦状态"
            )
        beneficiary_state = state_dict[beneficiary_obj.CID]
        return not beneficiary_state
