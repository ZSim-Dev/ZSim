from typing import TypeVar

from ....define import SkillSubEventTypes, SkillType, ZSimEventTypes
from ...Preload import SkillNode
from .base_zsim_event import BaseZSimEventContext, EventMessage, ExecutionEvent
from .base_zsim_event import ZSimBaseEvent as ZBE

T = TypeVar("T", bound=EventMessage)


class SkillEventMessage(EventMessage):
    skill_tag: str
    _preload_tick: int | None = None  # 技能加载的时刻(技能开始时刻)

    @property
    def preload_tick(self) -> int | None:
        return self._preload_tick

    @preload_tick.setter
    def preload_tick(self, value: int) -> None:
        if self._preload_tick is not None:
            raise ValueError("preload_tick 已经被设置过了")
        self._preload_tick = value


class SkillEventContext(BaseZSimEventContext):
    def __init__(self):
        super().__init__()
        self._is_active: bool = False
        self._hitted_count: int = 0
        self.preload_tick: int | None = None  # 【技能开始事件】发出的时刻

    @property
    def hitted_count(self) -> int:
        return self._hitted_count

    def hitted_count_inc(self) -> None:
        """技能命中计数加1"""
        self._hitted_count += 1

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value


class SkillEvent(ZBE[T]):
    """技能事件, 仅记录静态技能。在角色初始化时创建,被Character对象持有,在后续其他事件中被引用。"""

    @property
    def skill_type(self) -> SkillType:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.skill.skill_type


class SkillExecutionEvent(ExecutionEvent):
    """技能持续事件,构造时,封装一个SkillEvent"""

    def __init__(
        self,
        event_origin: SkillEvent[EventMessage],
        event_type: ZSimEventTypes,
        event_message: SkillEventMessage,
    ):
        super().__init__(
            event_origin=event_origin, event_type=event_type, event_message=event_message
        )

    @property
    def skill_type(self) -> SkillType:
        assert isinstance(self.event_origin, SkillEvent)
        return self.event_origin.skill_type

    @property
    def hit_times(self) -> int:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.hit_times

    @property
    def ticks(self) -> int:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.skill.ticks

    @property
    def hit_list(self) -> list[int | float] | None:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.skill.tick_list

    def get_timeline(self, preload_tick: int) -> dict[SkillSubEventTypes, list[int | float]]:
        """获取技能时间轴"""
        time_line: dict[SkillSubEventTypes, list[int | float]] = {}
        _hit_list = self.hit_list
        # 对于没有录入命中帧的技能，需要根据命中数量平均拆分、现场计算命中帧。
        if _hit_list is None:
            hit_times = self.hit_times
            step_length = (self.ticks - 1) / (hit_times + 1)
            hit_list = [preload_tick + i * step_length for i in range(hit_times + 1)]
        else:
            # 对于有录入命中帧的技能，直接使用录入的命中帧。
            hit_list = [preload_tick + i for i in _hit_list]
        start_tick = preload_tick
        end_tick = preload_tick + self.ticks
        time_line[SkillSubEventTypes.START] = [start_tick]
        time_line[SkillSubEventTypes.HIT] = hit_list
        time_line[SkillSubEventTypes.END] = [end_tick]
        return time_line
