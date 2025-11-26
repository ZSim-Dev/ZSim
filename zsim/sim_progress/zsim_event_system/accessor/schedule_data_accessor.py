from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...ScheduledEvent import ScheduleData


class ScheduleDataAccessor:
    def __init__(self, schedule_data: "ScheduleData"):
        """访问ScheduleData的接口,在一些EventContext构造时注入"""
        self._schedule_data = schedule_data

    @property
    def event_list(self) -> list[Any]:
        """
        获取event_list的接口,event_list会经常清空、重置,
        让对象直接持有list会导致list在传递过程中丢失,
        所以为了代码的一致性,这里必须套一层。
        """
        return self._schedule_data.event_list
