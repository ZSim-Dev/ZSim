"""Modernized buff engine for ZSim.

This package provides data definitions, registry access and runtime services for
handling buff lifecycle in the simulator.  The module is intentionally
decoupled from legacy Buff logic and can be adopted incrementally.
"""

from .definitions import (
    BuffDefinition,
    Trigger,
    Condition,
    Effect,
    TargetSelector,
    ConditionOperator,
)
from .registry import BuffRegistry
from .engine import (
    EventRouter,
    ConditionEvaluator,
    EffectExecutor,
    BuffEngine,
    BuffExecutionContext,
)
from .store import BuffInstance, BuffStore

__all__ = [
    "BuffDefinition",
    "Trigger",
    "Condition",
    "ConditionOperator",
    "Effect",
    "TargetSelector",
    "BuffRegistry",
    "EventRouter",
    "ConditionEvaluator",
    "EffectExecutor",
    "BuffEngine",
    "BuffExecutionContext",
    "BuffInstance",
    "BuffStore",
]
