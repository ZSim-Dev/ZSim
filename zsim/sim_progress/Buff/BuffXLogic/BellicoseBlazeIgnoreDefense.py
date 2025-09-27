from .. import Buff, JudgeTools, check_preparation


class BellicoseBlazeIgnoreDefenseRecord:
    def __init__(self):
        self.equipper = None
        self.char = None


class BellicoseBlazeIgnoreDefense(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是嚣枪喧焰无视防御力Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xstart = self.special_start_logic
        self.equipper = None
        self.buff_0 = None
        self.record: BellicoseBlazeIgnoreDefenseRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.equipper is None:
            self.equipper = JudgeTools.find_equipper(
                "嚣枪喧焰", sim_instance=self.buff_instance.sim_instance
            )
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )[self.equipper][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = BellicoseBlazeIgnoreDefenseRecord()
        self.record = self.buff_0.history.record

    def special_start_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(equipper="嚣枪喧焰")