from .. import Buff, JudgeTools, check_preparation
from define import ALICE_REPORT
from copy import deepcopy
from zsim.sim_progress.Preload import SkillNode


class AlicePolarizedAssaultTriggerRecord:
    def __init__(self):
        self.char = None
        self.allowed_skill_tag_list: list[str] = ["1401_SNA_3", "1401_Q"]        # 合法的极性强击触发源
        self.trigger_origin: "SkillNode | None" = None


class AlicePolarizedAssaultTrigger(Buff.BuffLogic):
    """爱丽丝的极性强击触发器"""
    def __init__(self, buff_instance):
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.xeffect = self.special_effect_logic
        self.buff_0 = None
        self.record: AlicePolarizedAssaultTriggerRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["爱丽丝"][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = AlicePolarizedAssaultTriggerRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs) -> bool:
        """极性强击的判断函数，放行三蓄和大招"""
        self.check_record_module()
        self.get_prepared(char_CID=1401)
        skill_node = kwargs.get("skill_node")
        if skill_node is None:
            return False
        if not isinstance(skill_node, SkillNode):
            return False
        if skill_node.skill_tag not in self.record.allowed_skill_tag_list:
            return False
        tick = self.buff_instance.sim_instance.tick
        if not skill_node.is_last_hit(tick=tick):
            return False
        # 小于2画时，大招无法触发极性强击
        if skill_node.skill_tag == "1401_Q" and self.record.char.cinema < 2:
            return False

        if self.record.trigger_origin is not None:
            raise ValueError(f"【极性强击触发器警告】存在尚未处理的触发源{self.record.trigger_origin.skill_tag}")
        self.record.trigger_origin = skill_node
        return True

    def special_effect_logic(self, **kwargs):
        """极性强击触发器的执行函数，构造一个极性强击事件并且将其添加进event_list中，同时置空自己的触发信号"""
        self.check_record_module()
        self.get_prepared(char_CID=1401)
        from zsim.sim_progress.data_struct import PolarizedAssaultEvent
        sim_instance = self.buff_instance.sim_instance
        tick = sim_instance.tick
        enemy = sim_instance.schedule_data.enemy
        copyed_anomaly_bar = deepcopy(enemy.anomaly_bars_dict[0])
        copyed_anomaly_bar.activated_by = self.record.trigger_origin
        event = PolarizedAssaultEvent(
            execute_tick=tick,
            anomlay_bar=copyed_anomaly_bar,
            char_instance=self.record.char,
            skill_node=self.record.trigger_origin)
        event_list = sim_instance.schedule_data.event_list
        event_list.append(event)
        if ALICE_REPORT:
            sim_instance.schedule_data.change_process_state()
            print(f"【爱丽丝事件】{self.record.trigger_origin.skill.skill_text} 最后一个Hit命中！触发了一次极性强击！")
        self.record.trigger_origin = None
