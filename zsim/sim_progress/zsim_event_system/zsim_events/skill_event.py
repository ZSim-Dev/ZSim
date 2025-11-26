from typing import TypeVar

from ....define import SkillSubEventTypes, SkillType
from ...data_struct import ZSimTimer
from ...Preload import SkillNode
from ..accessor import ScheduleDataAccessor
from .base_zsim_event import BaseZSimEventContext, EventMessage, ExecutionEvent
from .base_zsim_event import ZSimBaseEvent as ZBE

T = TypeVar("T", bound=EventMessage)


class SkillEventMessage(EventMessage):
    skill_tag: str
    _preload_tick: int | None = None  # 技能加载的时刻(技能开始时刻)
    _default_split: bool = True  # 是否按默认的平均规则来分段技能

    @property
    def preload_tick(self) -> int | None:
        return self._preload_tick

    @preload_tick.setter
    def preload_tick(self, value: int) -> None:
        if self._preload_tick is not None:
            raise ValueError("preload_tick 已经被设置过了")
        self._preload_tick = value

    @property
    def default_split(self) -> bool:
        return self._default_split

    @default_split.setter
    def default_split(self, value: bool) -> None:
        self._default_split = value


class SkillEventContext(BaseZSimEventContext):
    def __init__(self, timer: ZSimTimer, schedule_data_accessor: ScheduleDataAccessor):
        super().__init__()
        self._is_active: bool = False
        self._hitted_count: int = 0
        self.preload_tick: int | None = None  # 【技能开始事件】发出的时刻
        self.timer: ZSimTimer = timer
        self._schedule_data_accessor: ScheduleDataAccessor = schedule_data_accessor

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


class SkillEvent(ZBE[SkillEventMessage]):
    """技能事件, 仅记录静态技能。在角色初始化时创建,被Character对象持有,在后续其他事件中被引用。"""

    @property
    def skill_type(self) -> SkillType:
        assert isinstance(self.event_origin, SkillNode)
        return self.event_origin.skill.skill_type


class SkillExecutionEvent(ExecutionEvent[SkillEventMessage]):
    """技能持续事件,构造时,封装一个SkillEvent"""

    def __init__(
        self,
        event_origin: SkillEvent,
        event_type: SkillSubEventTypes,
        event_message: SkillEventMessage,
    ):
        super().__init__(
            event_origin=event_origin, event_type=event_type, event_message=event_message
        )

        self.time_line: dict[SkillSubEventTypes, list[int | float]] | None = None

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

    def _get_timeline(self, preload_tick: int) -> dict[SkillSubEventTypes, list[int | float]]:
        """获取技能的时间线"""
        from ..event_utools import cal_skill_time_line

        return cal_skill_time_line(
            preload_tick=preload_tick,
            hit_times=self.hit_times,
            ticks=self.ticks,
            hit_list=self.hit_list,
        )

    def skill_event_start(self) -> None:
        """初始化技能的时间线"""
        assert self.time_line is None, "时间线已经初始化过了"
        preload_tick = self.event_message.preload_tick
        assert preload_tick is not None, (
            "SkillExecutionEvent的skill_event_start方法必须依赖有效的preload_tick值"
        )
        self.time_line = self._get_timeline(preload_tick)

    def hit_check(self, context: SkillEventContext) -> bool:
        """技能命中时刻检查

        Args:
            context (SkillEventContext): 上下文,包含一个timer, 用于获取时间

        Returns:
            bool: 当前tick是否存在命中事件
        """
        assert context.timer is not None, "计时器尚未初始化"
        tick_now: int = context.timer.tick
        from ..event_utools import check_skill_hit_tick

        return check_skill_hit_tick(
            tick=tick_now, default_split=self.event_message.default_split, time_line=self.time_line
        )
