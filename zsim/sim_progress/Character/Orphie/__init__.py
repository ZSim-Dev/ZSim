from typing import TYPE_CHECKING

from zsim.sim_progress.Report import report_to_log

from ..character import Character
from ..utils.filters import _skill_node_filter
from .orphie_after_shock_attack_manager import OrphieAfterShockAttackManager as Oasam
from .zeroed_state_manager import ZeroedStateManager as Zsm

if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.simulator.simulator_class import Simulator


class Orphie(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bottled_heat: int | float = 100  # 畜炎初始100点
        self.max_bottled_heat: int = 125  # 最大125点
        self.after_shock_manager: Oasam = Oasam(self)
        self.zeroed_state_manager = Zsm(self)

    def special_resources(self, *args, **kwargs) -> None:
        """奥菲斯的特殊资源模块"""
        # 输入类型检查
        skill_nodes: list[SkillNode] = _skill_node_filter(*args, **kwargs)
        for nodes in skill_nodes:
            self.after_shock_manager.update_myself(skill_node=nodes)
            if nodes.char_name == self.NAME:
                # 首先更新畜炎
                self.update_bottled_heat(update_obj=nodes)

    def update_bottled_heat(self, update_obj: int | float | SkillNode) -> None:
        """更新畜炎"""
        bottled_heat: int | float = 0
        if isinstance(update_obj, int | float):
            self.bottled_heat = update_obj
        elif isinstance(update_obj, SkillNode):
            if update_obj.labels is None or update_obj.labels == {}:
                bottled_heat = 0
            else:
                if "bottled_heat" in update_obj.labels:
                    value = update_obj.labels["bottled_heat"]
                    assert isinstance(value, int | float), (
                        f"技能节点 {update_obj.skill.skill_text} 的标签 bottled_heat 类型错误，必须为 int 或 float，当前类型为 {type(value).__name__}"
                    )
                    bottled_heat = value
                else:
                    bottled_heat = 0
        else:
            raise TypeError(f"非法的更新对象类型：{type(update_obj).__name__}")
        if bottled_heat < 0:
            assert abs(bottled_heat) <= self.bottled_heat, (
                f"畜炎消耗（{bottled_heat:.1f}）超出当前值：{self.bottled_heat:.1f}点"
            )
        self.bottled_heat += bottled_heat
        self.bottled_heat = max(0, min(self.bottled_heat, self.max_bottled_heat))

    def POST_INIT_DATA(self, sim_instance: "Simulator"):
        pass

    def get_resources(self, *args, **kwargs) -> tuple[str | None, int | float | None]:
        return "蓄炎", self.bottled_heat

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        return {"追加攻击锁定状态": self.after_shock_manager.is_locked}
