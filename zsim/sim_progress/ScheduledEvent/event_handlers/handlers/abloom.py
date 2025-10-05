"""薇薇安异放事件处理器"""

from typing import Any

from zsim.sim_progress import Report
from zsim.sim_progress.anomaly_bar.CopyAnomalyForOutput import DirgeOfDestinyAnomaly as Abloom

from ...CalAnomaly import CalAbloom
from ..base import BaseEventHandler
from ..context import EventContext


class AbloomEventHandler(BaseEventHandler):
    """薇薇安异放事件处理器"""

    def __init__(self):
        super().__init__("abloom")

    def can_handle(self, event: Any) -> bool:
        return type(event) is Abloom

    def handle(self, event: Abloom, context: EventContext) -> None:
        """处理薇薇安异放事件"""
        enemy = self._get_context_enemy(context)
        dynamic_buff = self._get_context_dynamic_buff(context)
        sim_instance = self._get_context_sim_instance(context)
        tick = self._get_context_tick(context)

        # 计算异放伤害
        calculator = CalAbloom(
            abloom_obj=event,
            enemy_obj=enemy,
            dynamic_buff=dynamic_buff,
            sim_instance=sim_instance,
        )

        damage_anomaly = calculator.cal_anomaly_dmg()

        Report.report_dmg_result(
            tick=tick,
            element_type=event.element_type,
            skill_tag="异放",
            dmg_expect=round(damage_anomaly, 2),
            is_anomaly=True,
            dmg_crit=round(damage_anomaly, 2),
            stun=0,
            buildup=0,
            **enemy.dynamic.get_status(),
            UUID=event.UUID if event.UUID is not None else "",
        )
