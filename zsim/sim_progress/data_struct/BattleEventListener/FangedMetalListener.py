from typing import TYPE_CHECKING

from .BaseListenerClass import BaseListener
from zsim.models.event_enums import ListenerBroadcastSignal as LBS

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator


class FangedMetalListener(BaseListener):
    """这个监听器的作用是监听所有强击事件的触发，獠牙重金属4"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.buff_index = "Buff-驱动盘-獠牙重金属-增伤"

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到强击事件后，激活监听器"""
        if signal not in [LBS.ASSAULT_STATE_ON]:
            return
        self.listener_active(target=self.owner)

    def listener_active(self, **kwargs):
        """獠牙重金属4的监听器激活时，为佩戴者添加增伤buff"""
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy
        from zsim.sim_progress.Character.character import Character
        target = kwargs.get("target")
        assert isinstance(target, Character), "獠牙重金属4的监听器激活时，传入激活函数的target参数必须是Character类"
        benifit_list = [target.NAME]
        buff_add_strategy(self.buff_index, benifit_list=benifit_list, sim_instance=self.sim_instance)
