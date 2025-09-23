from .. import Buff, JudgeTools, check_preparation


class MoonlightLullabyAllTeamDmgBonusRecord:
    def __init__(self):
        self.equipper = None
        self.char = None


class MoonlightLullabyAllTeamDmgBonus(Buff.BuffLogic):
    def __init__(self, buff_instance):
        """这是月光骑士颂全队增伤Buff的脚本"""
        super().__init__(buff_instance)
        self.buff_instance: Buff = buff_instance
        self.xjudge = self.special_judge_logic
        self.equipper = None
        self.buff_0 = None
        self.record: MoonlightLullabyAllTeamDmgBonusRecord | None = None

    def get_prepared(self, **kwargs):
        return check_preparation(buff_instance=self.buff_instance, buff_0=self.buff_0, **kwargs)

    def check_record_module(self):
        if self.equipper is None:
            self.equipper = JudgeTools.find_equipper(
                "月光骑士颂", sim_instance=self.buff_instance.sim_instance
            )
        if self.buff_0 is None:
            self.buff_0 = JudgeTools.find_exist_buff_dict(
                sim_instance=self.buff_instance.sim_instance
            )[self.equipper][self.buff_instance.ft.index]
        if self.buff_0.history.record is None:
            self.buff_0.history.record = MoonlightLullabyAllTeamDmgBonusRecord()
        self.record = self.buff_0.history.record

    def special_judge_logic(self, **kwargs):
        self.check_record_module()
        self.get_prepared(equipper="月光骑士颂")