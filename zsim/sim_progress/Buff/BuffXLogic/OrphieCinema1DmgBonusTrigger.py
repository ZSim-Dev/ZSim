from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class OrphieCinema1DmgBonusTriggerRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.buff_index = "Buff-角色-奥菲斯-影画-1画-准星聚焦增伤"


class OrphieCinema1DmgBonusTrigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是奥菲斯影画1画准星聚焦增伤触发器Buff的脚本"""
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
            )["奥菲斯"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, (
            "【Buff初始化警告】奥菲斯的复杂逻辑模块未正确初始化，请检查函数"
        )
        if self.buff_0.history.record is None:
            self.buff_0.history.record = OrphieCinema1DmgBonusTriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """奥菲斯1画增伤效果的触发器"""
        self.check_record_module()
        self.get_prepared(char_CID=1301)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        assert self.record.char is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块中，角色实例未正确初始化，请检查函数"
        )
        from zsim.sim_progress.Character.Orphie import Orphie

        assert isinstance(self.record.char, Orphie)
        if any(
            [
                bool_value
                for bool_value in self.record.char.zeroed_state_manager.get_zeroed_state_group().values()
            ]
        ):
            return True
        return False


def special_hit_logic(self, **kwargs):
    self.check_record_module()
    self.get_prepared(char_CID=1301)
    assert self.record is not None, (
        f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
    )
    assert self.record.char is not None, (
        f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块中，角色实例未正确初始化，请检查函数"
    )
    from zsim.sim_progress.Character.Orphie import Orphie

    assert isinstance(self.record.char, Orphie)
    sim_instance = self.buff_instance.sim_instance
    assert sim_instance is not None
    state_dict: dict[int, bool] = self.record.char.zeroed_state_manager.get_zeroed_state_group()
    beneficiary_cid_list: list[int] = [cid for cid in state_dict.keys() if state_dict[cid]]
    beneficiary_name_list: list[str] = [
        obj.NAME for obj in sim_instance.char_data.char_obj_list if obj.CID in beneficiary_cid_list
    ]
    from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy

    buff_add_strategy(
        self.record.buff_index, benifit_list=beneficiary_name_list, sim_instance=sim_instance
    )
