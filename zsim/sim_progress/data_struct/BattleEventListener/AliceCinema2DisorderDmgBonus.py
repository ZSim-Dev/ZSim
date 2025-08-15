from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT
from ...anomaly_bar.CopyAnomalyForOutput import Disorder, PolarityDisorder
if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice


class AliceCinema2DisorderDmgBonus(BaseListener):
    """这个监听器的作用是监听紊乱事件来触发2画紊乱伤害提升Buff"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char:  "Character | None | Alice" = None
        self.buff_index = "Buff-角色-爱丽丝-影画-2画-紊乱伤害提升"

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到紊乱生成信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            self.char = char_obj
            if self.char.cinema < 2:
                raise ValueError(f"【爱丽丝2画监听器警告】检测到{self.char.cinema}画的爱丽丝企图创建2画相关监听器，请检查初始化函数。")
        
        if signal != LBS.DISORDER_SPAWN:
            return
        if not isinstance(event, Disorder | PolarityDisorder):
            print(f"【爱丽丝2画监听器警告】检测到紊乱生成信号(DISORDER_SPAWN)，但是与之匹配传入的不是紊乱或是极性紊乱类型，而是{type(event)}类型")
            return
        
        self.listener_active()

    def listener_active(self):
        """监听器的激活函数，为敌人添加紊乱伤害提升Buff"""
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy
        buff_add_strategy(self.buff_index, benifit_list=["enemy"], sim_instance=self.sim_instance)
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(f"【爱丽丝事件】【2画】监听到紊乱生成信号，为敌人添加了{self.buff_index}Buff！")
