from typing import TYPE_CHECKING
from zsim.models.event_enums import ListenerBroadcastSignal as LBS
from .BaseListenerClass import BaseListener
from zsim.define import ALICE_REPORT

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator
    from zsim.sim_progress.Character.character import Character
    from zsim.sim_progress.Character.Alice import Alice
    from zsim.sim_progress.anomaly_bar import AnomalyBar


class AliceCinema1DefReduceListener(BaseListener):
    """该监听器是爱丽丝第一影画的强击Buff的监听器，当监听到强击生成信号时，给敌人挂上减防debuff"""

    def __init__(self, listener_id: str | None = None, sim_instance: "Simulator | None" = None):
        super().__init__(listener_id, sim_instance=sim_instance)
        self.char: "Character | None | Alice" = None
        self.buff_index = "Buff-角色-爱丽丝-影画-1画-减防"

    def listening_event(self, event: "AnomalyBar", signal: LBS, **kwargs):
        """监听到紊乱信号时，激活"""
        if self.char is None:
            char_obj = self.sim_instance.char_data.find_char_obj(CID=1401)
            assert char_obj is not None, (
                "【爱丽丝1画监听器警告】检测到爱丽丝1画相关监听器初始化时，无法找到爱丽丝对象，请检查初始化函数。"
            )
            self.char = char_obj
            if self.char.cinema < 1:
                raise ValueError(
                    f"【爱丽丝1画监听器警告】检测到{self.char.cinema}画的爱丽丝企图创建1画相关监听器，请检查初始化函数。"
                )
        # 过滤掉非爱丽丝激活的强击事件
        if signal not in [LBS.ASSAULT_SPAWN, LBS.POLARIZED_ASSAULT_SPAWN]:
            return
        else:
            from zsim.sim_progress.Preload import SkillNode

            assert isinstance(event.activated_by, SkillNode), (
                "【爱丽丝1画监听器警告】检测到爱丽丝1画相关监听器激活时，传入的异常条的Activated_by属性为None"
            )
            if event.activated_by.char_name != "爱丽丝":
                return
        self.listener_active()

    def listener_active(self, **kwargs):
        from zsim.sim_progress.Buff.BuffAddStrategy import buff_add_strategy

        buff_add_strategy(self.buff_index, benifit_list=["enemy"], sim_instance=self.sim_instance)
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print("【爱丽丝事件】【1画】检测到爱丽丝触发强击，目标防御力在接下来的30秒内降低20%")
