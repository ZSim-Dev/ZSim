from math import floor
from typing import TYPE_CHECKING
from zsim.define import ALICE_REPORT
from zsim.sim_progress.Report import report_to_log

from .character import Character
from .utils.filters import _skill_node_filter

if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.simulator.simulator_class import Simulator


class Alice(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blade_etiquette: float = 300.0  # 剑仪
        self.max_blade_etiquette: float = 300.0  # 最大剑仪值
        self.victory_state_update_tick: int = 0         # 六画的决胜状态的更新时间
        self.victory_state_duration: int = 1800         # 决胜状态持续时间
        self.victory_state_activation_origin: list[str] = ["1401_SNA_3", "1401_Q"]      # 决胜状态激活源
        self.victory_state_attack_counter: int = 0       # 六画的决胜状态的剩余攻击次数
        self.victory_state_max_attack_count: int = 6     # 六画的决胜状态的最大攻击次数

    @property
    def victory_state(self) -> bool:
        """决胜状态是否处于激活状态"""
        if self.victory_state_update_tick == 0 or self.victory_state_attack_counter == 0:
            return False
        else:
            # 层数没耗尽时，才检查时间条件
            return self.sim_instance.tick - self.victory_state_update_tick < self.victory_state_duration

    @property
    def blade_etquitte_bar(self) -> int:
        # 剑仪条格子数
        return floor(self.blade_etiquette/100)

    def special_resources(self, *args, **kwargs) -> None:
        """爱丽丝的特殊资源模块"""
        # 输入类型检查
        skill_nodes: list[SkillNode] = _skill_node_filter(*args, **kwargs)
        for node in skill_nodes:
            if node.char_name == self.NAME:
                # 6画情况下，优先更新决胜状态的相关参数
                if self.cinema == 6:
                    if node.skill_tag in self.victory_state_activation_origin:
                        self.victory_state_update_tick = self.sim_instance.tick
                        self.victory_state_attack_counter = self.victory_state_max_attack_count
                        if ALICE_REPORT:
                            self.sim_instance.schedule_data.change_process_state()
                            print(f"【爱丽丝事件】【6画】检测到爱丽丝释放了{node.skill.skill_text}，激活了决胜状态")
                # 更新剑仪值
                self.update_blade_etiquette(update_obj=node)
            else:
                # 队友的skill_node判断；
                pass

    def update_blade_etiquette(self, update_obj: SkillNode | float | int) -> None:
        # 更新剑仪值的函数
        if update_obj is None:
            raise ValueError(f"【剑仪值更新警告】在调用剑仪值更新函数时，必须传入update_obj参数")
        if isinstance(update_obj, SkillNode):
            if update_obj.labels is None:
                raise ValueError(f"【剑仪值更新警告】传入的{update_obj.skill_tag}没有初始化label参数，请检查数据库")
            if "blade_etiquette" not in update_obj.labels:
                print(f"【剑仪值更新警告】技能{update_obj.skill_tag}的label中不包含剑仪值，请检查数据库")
                return
            blade_etiquette = update_obj.labels.get("blade_etiquette", 0)
        elif isinstance(update_obj, float | int):
            blade_etiquette = update_obj
        self.blade_etiquette = min(self.max_blade_etiquette, self.blade_etiquette + blade_etiquette)
        if ALICE_REPORT:
            self.sim_instance.schedule_data.change_process_state()
            print(f"【爱丽丝事件】爱丽丝 {"恢复" if blade_etiquette >= 0 else "消耗"} 了 {abs(blade_etiquette):.2f} 点剑仪值，当前剑仪值为 {self.blade_etiquette:.2f}")

    def POST_INIT_DATA(self, sim_insatnce: "Simulator"):
        """初始化爱丽丝的监听器组"""
        listener_manager = sim_insatnce.listener_manager
        # 组队被动激活时，初始化紊乱回剑仪值的监听器
        if self.additional_abililty_active:
            listener_manager.listener_factory(listener_owner=self, initiate_signal="Alice_1", sim_instance=sim_insatnce)

        # 初始化本体固有监听器（紊乱倍率、物理积蓄效率）
        for listener_id in ["Alice_2", "Alice_3"]:
            listener_manager.listener_factory(listener_owner=self, initiate_signal=listener_id, sim_instance=sim_insatnce)

        # 1画激活时，初始化1画监听器（减防Buff）
        if self.cinema >= 1:
            listener_manager.listener_factory(listener_owner=self, initiate_signal="Alice_Cinema_1_A", sim_instance=sim_insatnce)
            listener_manager.listener_factory(listener_owner=self, initiate_signal="Alice_Cinema_1_B", sim_instance=sim_insatnce)
        
        # 2画激活时，初始化2画监听器（紊乱伤害提升）
        if self.cinema >= 2:
            listener_manager.listener_factory(listener_owner=self, initiate_signal="Alice_Cinema_2_A", sim_instance=sim_insatnce)

    def spawn_extra_attack(self):
        """6画额外攻击的接口，向Preload添加一次额外攻击事件，同时扣除一次使用次数"""
        pass

    def get_resources(self, *args, **kwargs) -> tuple[str, int]:
        return "剑仪格", self.blade_etquitte_bar

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        return {"剑仪值": self.blade_etiquette}
