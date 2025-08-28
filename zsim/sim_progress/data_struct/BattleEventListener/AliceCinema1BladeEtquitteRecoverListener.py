from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.Alice import Alice


class AliceCinema1BladeEtquitteRecoverListener(BaseListener):
    """该监听器是爱丽丝第一影画的剑仪值回复监听器"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Alice | None" = None
        self.blade_etquitte_value = 25

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到极性强击信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            from zsim.sim_progress.Character.Alice import Alice

            if not isinstance(char_obj, Alice):
                raise TypeError(
                    f"【爱丽丝1画监听器警告】获取的角色不是Alice类型，而是{type(char_obj)}"
                )
            self.char = char_obj
            if self.char.cinema < 1:
                raise ValueError(
                    f"【爱丽丝1画监听器警告】检测到{self.char.cinema}画的爱丽丝企图创建1画相关监听器，请检查初始化函数。"
                )

        if signal != LBS.POLARIZED_ASSAULT_SPAWN:
            return

        self.listener_active()

    def listener_active(self, **kwargs):
        if self.char is not None:
            if ALICE_REPORT:
                self.sim_instance.schedule_data.change_process_state()
                print(
                    f"【爱丽丝事件】【1画】监听到极性强击信号，即将为爱丽丝回复{self.blade_etquitte_value}点剑仪值！"
                )
            self.char.update_blade_etiquette(update_obj=self.blade_etquitte_value)
