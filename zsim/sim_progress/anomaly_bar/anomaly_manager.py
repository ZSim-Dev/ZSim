from typing import TYPE_CHECKING

from zsim.define import ELEMENT_TYPE_MAPPING

from . import (
    AuricInkAnomaly,
    ElectricAnomaly,
    EtherAnomaly,
    FireAnomaly,
    FrostAnomaly,
    IceAnomaly,
    PhysicalAnomaly,
)
from .AnomalyBarClass import AnomalyBar

if TYPE_CHECKING:
    from zsim.simulator.simulator_class import Simulator


class AnomalyRequiredContext:
    """异常条所需的上下文信息"""

    def __init__(self, sim_instance: "Simulator"):
        self.sim_instance = sim_instance

    def get_sim_instance(self) -> "Simulator":
        return self.sim_instance

    def get_current_tick(self) -> int:
        return self.sim_instance.tick


class AnomalyManager:
    """异常条管理器，管理整个ZSim的异常系统，包括异常条的初始化、更新、触发、紊乱等"""

    def __init__(self, anomaly_context: AnomalyRequiredContext):
        self.context = anomaly_context
        self.anomaly_bars_dict: dict[int, AnomalyBar] = {}
        self.anomaly_class_map: dict[int, type] = {
            0: PhysicalAnomaly,
            1: FireAnomaly,
            2: IceAnomaly,
            3: ElectricAnomaly,
            4: EtherAnomaly,
            5: FrostAnomaly,
            6: AuricInkAnomaly,
        }
        self.__initialize_anomaly_bars()

    def __initialize_anomaly_bars(self):
        """初始化异常条"""
        assert self.anomaly_bars_dict == {}, "异常条已经初始化过了"
        for element_type in ELEMENT_TYPE_MAPPING.keys():
            self.anomaly_bars_dict[element_type] = self.anomaly_class_map[element_type](
                sim_instance=self.context.get_sim_instance()
            )

    def update_max_buildup(self, value: int, element_type: int | None = None):
        """更新异常条的最大值"""
        assert self.anomaly_bars_dict, "异常条未初始化"
        if element_type is None:
            # 更新所有异常条的最大值
            for anomaly_bar in self.anomaly_bars_dict.values():
                anomaly_bar.max_anomaly = value
        else:
            # 更新指定异常条的最大值
            self.anomaly_bars_dict[element_type].max_anomaly = value

    def update_build_up(self):
        pass
