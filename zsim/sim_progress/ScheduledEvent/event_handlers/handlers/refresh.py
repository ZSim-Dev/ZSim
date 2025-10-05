"""数据刷新事件处理器"""

from typing import Any

from zsim.sim_progress.data_struct import ScheduleRefreshData

from ..base import BaseEventHandler
from ..context import EventContext


class RefreshEventHandler(BaseEventHandler):
    """数据刷新事件处理器"""

    def __init__(self):
        super().__init__("refresh")

    def can_handle(self, event: Any) -> bool:
        return isinstance(event, ScheduleRefreshData)

    def handle(self, event: ScheduleRefreshData, context: EventContext) -> None:
        """处理数据刷新事件"""
        try:
            data = self._get_context_data(context)

            # 创建角色映射
            char_mapping = {character.NAME: character for character in data.char_obj_list}

            # 更新能量
            for target in event.sp_target:
                if target != "":
                    if target not in char_mapping:
                        raise KeyError(f"目标角色 {target} 未找到")
                    char_mapping[target].update_sp(event.sp_value)

            # 更新喧响
            for target in event.decibel_target:
                if target != "":
                    if target not in char_mapping:
                        raise KeyError(f"目标角色 {target} 未找到")
                    char_mapping[target].update_decibel(event.decibel_value)

        except Exception as e:
            self._handle_error(e, "数据刷新事件处理", event)
