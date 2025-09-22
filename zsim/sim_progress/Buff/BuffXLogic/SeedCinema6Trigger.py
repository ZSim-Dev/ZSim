from zsim.define import SEED_REPORT

from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class SeedCinema6TriggerRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.cd = 180
        self.additional_damage_skill_tag = "1461_Cinema_6"
        self.trigger_skill_tag = "1461_SNA_1"


class SeedCinema6Trigger(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是席德6画触发器Buff的脚本"""
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
            )["席德"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, (
            "【Buff初始化警告】席德的复杂逻辑模块未正确初始化，请检查函数"
        )
        if self.buff_0.history.record is None:
            self.buff_0.history.record = SeedCinema6TriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None, (
            f"【Buff初始化警告】{self.buff_instance.ft.index}的复杂逻辑模块未正确初始化，请检查函数"
        )
        skill_node = kwargs.get("skill_node", None)
        if skill_node is None:
            return False
        from zsim.sim_progress.Preload import SkillNode
        assert isinstance(skill_node, SkillNode)
        if skill_node.skill_tag != self.record.trigger_skill_tag:
            return False
        tick = self.buff_instance.sim_instance.tick
        if tick != skill_node.preload_tick:
            return False
        if not self.record.check_cd(tick_now=tick):
            return False
        return True

    def special_start_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(char_CID=1461)
        assert self.record is not None
        from zsim.sim_progress.data_struct.SchedulePreload import schedule_preload_event_factory
        tick = self.buff_instance.sim_instance.tick
        preload_tick_list = [tick, tick, tick]
        skill_tag_list = [self.record.additional_damage_skill_tag] * 3
        preload_data = self.buff_instance.sim_instance.preload.preload_data
        schedule_preload_event_factory(
            preload_tick_list=preload_tick_list,
            skill_tag_list=skill_tag_list,
            preload_data=preload_data,
            sim_instance=self.buff_instance.sim_instance
        )
        self.record.last_active_tick = tick
        if SEED_REPORT:
            self.buff_instance.sim_instance.schedule_data.change_process_state()
            print("【席德6画】检测到席德发动了 落华·重戮，添加三次协同攻击！")

