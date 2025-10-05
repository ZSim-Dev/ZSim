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


class AnomalyManager:
    """异常条管理器，管理整个ZSim的异常系统！"""

    def __init__(self):
        self.anomaly_bars_group: dict[int, AnomalyBar] = {}
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
        assert self.anomaly_bars_group == {}, "异常条已经初始化过了"
        for element_type in ELEMENT_TYPE_MAPPING.keys():
            self.anomaly_bars_group[element_type] = self.anomaly_class_map[element_type](
                sim_instance=self.sim_instance
            )

    def update_max_buildup(self, element_type: int, value: int | float):
        """更新异常条的最大值"""
        pass


