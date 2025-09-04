from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice
    from zsim.sim_progress.anomaly_bar import AnomalyBar


class AliceCoreSkillPhyBuildupBonusListener(BaseListener):
    """这个监听器的作用是监听强击事件，并且为爱丽丝添加Buff"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Character | None | Alice" = None
        self.buff_index = "Buff-角色-爱丽丝-核心被动-物理异常积蓄效率提升"

    def listening_event(self, event: "AnomalyBar", signal: LBS, **kwargs):
        """监听到强击触发信号时激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            self.char = char_obj
        if signal in [LBS.ASSAULT_SPAWN, LBS.POLARIZED_ASSAULT_SPAWN]:
            if signal == LBS.ASSAULT_SPAWN:
                # 过滤不是爱丽丝自己触发的普通强击
                from zsim.sim_progress.Preload import SkillNode

                assert isinstance(event.activated_by, SkillNode), (
                    "【爱丽丝物理积蓄效率监听器警告】检测到监听器激活时，传入的异常条的Activated_by属性为None"
                )
                if event.activated_by.char_name != "爱丽丝":
                    return
            self.listener_active(signal=signal)

    def listener_active(self, **kwargs):
        """监听器的激活函数，为爱丽丝添加积蓄效率Buff"""
        signal = kwargs.get("signal")
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy

        buff_add_strategy(self.buff_index, benifit_list=["爱丽丝"], sim_instance=self.sim_instance)
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(f"【爱丽丝事件】检测到爱丽丝触发{"强击" if signal == LBS.ASSAULT_SPAWN else "极性强击"}，为爱丽丝添加 物理积蓄效率提高 的Buff")
