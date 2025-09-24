from typing import TYPE_CHECKING

from zsim.sim_progress.Report import report_to_log

from ..character import Character
from ..utils.filters import _skill_node_filter

if TYPE_CHECKING:
    from zsim.sim_progress.Preload import SkillNode
    from zsim.simulator.simulator_class import Simulator


class Orphie(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def special_resources(self, *args, **kwargs) -> None:
        """奥菲斯的特殊资源模块"""
        # 输入类型检查
        skill_nodes: list[SkillNode] = _skill_node_filter(*args, **kwargs)
        pass

    def POST_INIT_DATA(self, sim_instance: "Simulator"):
        pass

    def get_resources(self, *args, **kwargs) -> tuple[str | None, int | float | None]:
        pass

    def get_special_stats(self, *args, **kwargs) -> dict[str | None, object | None]:
        pass
