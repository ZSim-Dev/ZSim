import math
from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT
from ...anomaly_bar.CopyAnomalyForOutput import Disorder, PolarityDisorder

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice


class AliceCoreSkillDisorderBasicMulBonusListener(BaseListener):
    """这个监听器的作用是监听紊乱事件来触发Buff，并且根据当前物理异常的剩余时间，设定Buff的层数"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Character | None | Alice" = None
        self.buff_index = "Buff-角色-爱丽丝-核心被动-紊乱基础倍率增加"

    def listening_event(self, event, signal: LBS, **kwargs):
        """监听到紊乱触发信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            self.char = char_obj
        if signal not in [LBS.DISORDER_SPAWN]:
            return
        if not isinstance(signal, Disorder | PolarityDisorder):
            print(
                f"【爱丽丝紊乱监听器警告】检测到紊乱触发信号(DISORDER_SPAWN)，但是与之匹配传入的不是紊乱或是极性紊乱类型，而是{type(event)}类型"
            )
            return
        # 当传入的紊乱不是物理属性时直接返回。
        if event.element_type != 0:
            return
        self.listener_active(event_obj=event)

    def listener_active(self, **kwargs):
        """监听器的激活函数，根据当前紊乱的剩余时间，设定Buff层数"""
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy

        assert "event_obj" in kwargs, (
            "【爱丽丝紊乱监听器警告】监听器函数激活时，并未传入对应的event_obj参数！"
        )
        event_obj: Disorder | PolarityDisorder = kwargs["event_obj"]

        rest_tick = event_obj.remaining_tick()
        count = min(rest_tick / 60, 10)  # 最大层数10
        buff_add_strategy(
            self.buff_index,
            benifit_list=["enemy"],
            specified_count=count,
            sim_instance=self.sim_instance,
        )
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(
                f"【爱丽丝事件】检测到物理属性的紊乱结算，物理异常的剩余时间为{rest_tick:.1f}tick，使本次紊乱的基础倍率提升 {count * 18:.1f} %！"
            )
