from zsim.define import ORPHIE_REPORT

from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class OrphieCinema2DecibelRecoverTriggerRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.cd = 240
        self.decibel_recover_value = 65


class OrphieCinema2DecibelRecoverTrigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是奥菲斯影画2画喧响恢复触发器Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.xstart = self.special_start_logic
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
            self.buff_0.history.record = OrphieCinema2DecibelRecoverTriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """奥菲斯2画喧响恢复效果的触发器"""
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
        skill_node = kwargs.get("skill_node", None)
        if skill_node is None:
            return False
        from zsim.sim_progress.Preload import SkillNode

        assert isinstance(skill_node, SkillNode)
        # 筛选掉不是自己的技能
        if skill_node.char_name != self.record.char.NAME:
            return False
        # 筛选掉不是追击类型的技能
        if not skill_node.is_after_shock_attack:
            return False
        sim_instance = self.buff_instance.sim_instance
        assert sim_instance is not None
        # 筛选掉不是技能发动的时间点
        if skill_node.preload_tick != sim_instance.tick:
            return False
        # 筛选掉内置CD未就绪的情况
        if not self.record.check_cd(tick_now=sim_instance.tick):
            return False
        return True

    def special_start_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1301)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        assert self.record.char is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块中，角色实例未正确初始化，请检查函数"
        )
        from zsim.sim_progress.data_struct.sp_update_data import ScheduleRefreshData

        event = ScheduleRefreshData(
            decibel_target=(self.record.char.NAME,), decibel_value=self.record.decibel_recover_value
        )
        sim_instance = self.buff_instance.sim_instance
        assert sim_instance is not None
        event_list = sim_instance.schedule_data.event_list
        event_list.append(event)
        self.record.last_active_tick = sim_instance.tick
        if ORPHIE_REPORT:
            sim_instance.schedule_data.change_process_state()
            print(
                f"【奥菲斯2画】检测到奥菲斯发动追加攻击，为她恢复 {self.record.decibel_recover_value} 点喧响值"
            )
