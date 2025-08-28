from dataclasses import dataclass
from typing import TYPE_CHECKING

from .. import Dot

if TYPE_CHECKING:
    from zsim.sim_progress.anomaly_bar.AnomalyBarClass import AnomalyBar
    from zsim.simulator.simulator_class import Simulator


class AliceCoreSkillAssaultDot(Dot):
    def __init__(self, bar: "AnomalyBar | None" = None, sim_instance: "Simulator | None" = None):
        super().__init__(bar=bar, sim_instance=sim_instance)  # 调用父类Dot的初始化方法
        self.ft = self.DotFeature(sim_instance=sim_instance)
        if sim_instance is None:
            raise ValueError("构造dot实例时必须传入有效的sim_instance实例")

        from zsim.sim_progress.anomaly_bar.AnomalyBarClass import AnomalyBar
        # 正确性验证
        if any([bar is None,
                bar is not None and not isinstance(bar, AnomalyBar),
                bar.element_type != 0]):
            raise ValueError("构造爱丽丝的核心被动Dot实例时，必须传入有效的 物理属性 anomlay_bar 实例")
        self.anomaly_data = bar
        self.anomaly_data.rename_tag = "爱丽丝强击Dot"
        self.anomaly_data.scaling_factor = 0.025     # 缩放比例

    @dataclass
    class DotFeature(Dot.DotFeature):
        sim_instance: "Simulator | None"
        update_cd: int | float = 57         # dot的内置CD是0.95秒，换算为57帧
        index: str | None = "AliceCoreSkillAssaultDot"
        name: str | None = "爱丽丝物理异常Dot"
        dot_from: str | None = "爱丽丝"
        effect_rules: int | None = 1
        max_count: int | None = 999999
        incremental_step: int | None = 1
        max_duration: int | None = 999999
        complex_exit_logic = True           # 该dot为复杂退出逻辑

    def exit_judge(self, **kwargs):
        """爱丽丝物理异常Dot 的退出逻辑：敌人的只要不处于畏缩状态，就退出。"""
        enemy = kwargs.get("enemy", None)
        from zsim.sim_progress.Enemy import Enemy
        if not isinstance(enemy, Enemy):
            raise TypeError("enemy参数必须是Enemy类的实例")
        if not enemy.dynamic.assault:
            self.dy.active = False
            return True
        return False
