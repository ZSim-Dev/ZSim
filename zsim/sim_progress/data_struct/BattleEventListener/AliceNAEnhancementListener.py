from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice


class AliceNAEnhancementListener(BaseListener):
    """这个监听器的作用是监听强击的触发，触发后打开爱丽丝的强化平A状态"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Character | None | Alice" = None

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到紊乱信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            self.char = char_obj
        if signal not in [LBS.ASSAULT_SPAWN]:
            return
        self.listener_active()

    def listener_active(self, **kwargs):
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print("【爱丽丝事件】监听到强击事件触发！爱丽丝获得1次强化A5次数")
        from zsim.sim_progress.Character.Alice import Alice
        assert isinstance(self.char, Alice)
        self.char.na_enhancement_state = True
