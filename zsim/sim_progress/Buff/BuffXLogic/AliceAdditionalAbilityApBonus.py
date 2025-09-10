from .. import Buff, JudgeTools, check_preparation
from ._buff_record_base_class import BuffRecordBaseClass as BRBC


class AliceAdditionalAbilityApBonusRecord(BRBC):
    def __init__(self):
        super().__init__()
        self.trans_ratio: float = 1.6  # 转化比率


class AliceAdditionalAbilityApBonus(Buff.BuffLogic):
    def __init__(self, buff_instance: Buff):
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xhit = self.special_hit_logic
        self.buff_0: "Buff | None" = None
        self.record: BRBC | None = None

    def get_prepared(self, **kwargs):
        assert self.buff_0 is not None, "buff_0未初始化"
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["爱丽丝"][self.buff_instance.ft.index]
        assert self.buff_0 is not None, "buff_0未初始化"
        if self.buff_0.history.record is None:
            self.buff_0.history.record = AliceAdditionalAbilityApBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """根据触发时的异常掌控，计算转化的Buff层数"""
        self.check_record_module()
        self.get_prepared(char_CID=1401, sub_exist_buff_dict=1, enemy=1, dynamic_buff_list=1)
        assert self.record is not None, "记录模块未初始化"
        assert self.record.enemy is not None, "敌人未初始化"
        assert self.record.dynamic_buff_list is not None, "动态Buff列表未初始化"
        assert self.record.sub_exist_buff_dict is not None, "子存在Buff字典未初始化"

        from zsim.sim_progress.ScheduledEvent import Calculator

        mul_data = MultiplierData(
            enemy_obj=self.record.enemy,
            dynamic_buff=self.record.dynamic_buff_list,
            character_obj=self.record.char,
        )
        am = Calculator.AnomalyMul.cal_am(mul_data)
        if am < 140:
            return
        count = (am - 140) * self.record.trans_ratio
        tick = self.buff_instance.sim_instance.tick
        self.buff_instance.simple_start(
            timenow=tick, sub_exist_buff_dict=self.record.sub_exist_buff_dict, no_count=1
        )
        self.buff_instance.dy.count = count
        self.buff_instance.update_to_buff_0(buff_0=self.buff_0)
