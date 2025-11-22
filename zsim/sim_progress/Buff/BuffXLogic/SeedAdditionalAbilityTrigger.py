# 这是席德额外能力重击大招增伤无视电抗Buff的脚本
from define import SEED_REPORT

from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedAdditionalAbilityTriggerRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.cd = 60
        self.energy_value = 2  # 回能值，2点能量。


class SeedAdditionalAbilityTrigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是席德额外能力给正兵回能的触发器"""
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
            self.buff_0.history.record = SeedAdditionalAbilityTriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        skill_node = kwargs.get("skill_node")
        if skill_node is None:
            return False
        from zsim.sim_progress.Preload import SkillNode

        assert isinstance(skill_node, SkillNode)
        preload_data = self.buff_instance.sim_instance.preload.preload_data
        # 当前操作角色不是席德时，直接返回False
        if preload_data.operating_now != 1461:
            return False
        # 过滤掉不是席德的技能
        if skill_node.char_name != self.record.char.NAME:
            return False
        # 过滤掉所有非命中帧
        tick = self.buff_instance.sim_instance.tick
        if not skill_node.is_hit_now(tick=tick):
            return False
        # 检查内置CD
        if not self.record.check_cd(tick_now=tick):
            return False
        return True

    def special_hit_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert isinstance(self.record, SeedAdditionalAbilityTriggerRecord), (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        assert self.record.char.vanguard is not None, (
            "席德在激活了组队被动的情况下没有指定正兵，请检查"
        )
        vanguard = self.record.char.vanguard
        from zsim.sim_progress.data_struct.sp_update_data import ScheduleRefreshData

        energy_value = self.record.energy_value
        refresh_data = ScheduleRefreshData(
            sp_target=(vanguard.NAME,),
            sp_value=energy_value,
        )
        event_list = self.buff_instance.sim_instance.schedule_data.event_list
        event_list.append(refresh_data)
        self.record.last_active_tick = self.buff_instance.sim_instance.tick
        if SEED_REPORT:
            self.buff_instance.sim_instance.schedule_data.change_process_state()
            print(f"【席德事件】额外能力触发，为{vanguard}回恢 {energy_value} 点能量")
