from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice


class AliceDisorderListener(BaseListener):
    """这个监听器的作用是监听紊乱的触发"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Character | None | Alice" = None
        self.update_value = 30

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到紊乱信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            self.char = char_obj
        if signal not in [LBS.DISORDER_SETTLED]:
            return
        from ...anomaly_bar.CopyAnomalyForOutput import Disorder, PolarityDisorder

        if not isinstance(signal, Disorder | PolarityDisorder):
            print(
                f"【爱丽丝紊乱监听器警告】检测到紊乱结算信号(DISORDER_SETTLED)，但是与之匹配传入的不是紊乱或是极性紊乱类型，而是{type(event)}类型"
            )
            return
        self.listener_active()

    def listener_active(self, **kwargs):
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(
                f"【爱丽丝事件】紊乱监听器监听到紊乱结算，即将为爱丽丝回复{self.update_value}点剑仪值！"
            )
        assert isinstance(self.char, Alice)
        self.char.update_blade_etiquette(update_obj=self.update_value)
