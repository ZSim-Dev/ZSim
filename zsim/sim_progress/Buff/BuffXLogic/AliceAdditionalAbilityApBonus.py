from .. import Buff, JudgeTools, check_preparation


class AliceAdditionalAbilityApBonusRecord:
    def __init__(self):
        self.char = None
        self.sub_exist_buff_dict = None
        self.dynamic_buff_list = None
        self.enemy = None
        self.trans_ratio = 1.6      # 转化比率


class AliceAdditionalAbilityApBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xhit = self.special_hit_logic
        self.buff_0 = None
        self.record: AliceAdditionalAbilityApBonusRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )["爱丽丝"][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = AliceAdditionalAbilityApBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        """根据触发时的异常掌控，计算转化的Buff层数"""
        self.check_record_module()
        self.get_prepared(char_CID=1401, sub_exist_buff_dict=1, enemy=1, dynamic_buff_list=1)
        from zsim.sim_progress.ScheduledEvent.Calculator import MultiplierData
        from zsim.sim_progress.ScheduledEvent import Calculator
        mul_data = MultiplierData(
            self.record.enemy, self.record.dynamic_buff_list, self.record.char
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

