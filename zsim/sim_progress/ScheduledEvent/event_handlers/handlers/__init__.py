"""事件处理器模块

该模块包含所有具体的事件处理器实现和工厂类。
"""

from .abloom import AbloomEventHandler
from .anomaly import AnomalyEventHandler
from .disorder import DisorderEventHandler
from .factory import event_handler_factory
from .polarity_disorder import PolarityDisorderEventHandler
from .polarized_assault import PolarizedAssaultEventHandler
from .preload import PreloadEventHandler
from .quick_assist import QuickAssistEventHandler
from .refresh import RefreshEventHandler
from .skill import SkillEventHandler
from .stun_forced_termination import StunForcedTerminationEventHandler


def register_all_handlers() -> None:
    """注册所有事件处理器"""
    handlers = [
        SkillEventHandler(),
        AnomalyEventHandler(),
        DisorderEventHandler(),
        PolarityDisorderEventHandler(),
        AbloomEventHandler(),
        RefreshEventHandler(),
        QuickAssistEventHandler(),
        PreloadEventHandler(),
        StunForcedTerminationEventHandler(),
        PolarizedAssaultEventHandler(),
    ]

    for handler in handlers:
        event_handler_factory.register_handler(handler)


__all__ = [
    "SkillEventHandler",
    "AnomalyEventHandler",
    "DisorderEventHandler",
    "PolarityDisorderEventHandler",
    "AbloomEventHandler",
    "RefreshEventHandler",
    "QuickAssistEventHandler",
    "PreloadEventHandler",
    "StunForcedTerminationEventHandler",
    "PolarizedAssaultEventHandler",
    "event_handler_factory",
    "register_all_handlers",
]
