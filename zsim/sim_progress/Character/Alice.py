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
        # 初始化紊乱回复剑仪值的监听器（组队被动激活时）
        if self.additional_abililty_active:
            sim_insatnce.listener_manager.listener_factory(listener_owner=self, initiate_signal="Alice_1", sim_instance=sim_insatnce)
        for listener_id in ["Alice_2", "Alice_3"]:
            sim_insatnce.listener_manager.listener_factory(listener_owner=self, initiate_signal=listener_id, sim_instance=sim_insatnce)

    def get_resources(self, *args, **kwargs) -> tuple[str, int]:
        return "剑仪格", self.blade_etquitte_bar

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        return {"剑仪值": self.blade_etiquette}
