"""Data definitions for the modern buff engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

from pydantic import BaseModel, ConfigDict


class ConditionOperator(StrEnum):
    """Supported operators when evaluating conditions."""

    ALWAYS = "always"
    NEVER = "never"
    COMPARISON = "comparison"
    AND = "and"
    OR = "or"
    NOT = "not"


_COMPARATORS: Mapping[str, Callable[[Any, Any], bool]] = {
    "==": lambda lhs, rhs: lhs == rhs,
    "!=": lambda lhs, rhs: lhs != rhs,
    ">": lambda lhs, rhs: lhs is not None and rhs is not None and lhs > rhs,
    ">=": lambda lhs, rhs: lhs is not None and rhs is not None and lhs >= rhs,
    "<": lambda lhs, rhs: lhs is not None and rhs is not None and lhs < rhs,
    "<=": lambda lhs, rhs: lhs is not None and rhs is not None and lhs <= rhs,
    "in": lambda lhs, rhs: lhs in rhs if rhs is not None else False,
    "not_in": lambda lhs, rhs: lhs not in rhs if rhs is not None else True,
}


@dataclass(frozen=True, slots=True)
class Condition:
    """Declarative condition tree used by the :class:`ConditionEvaluator`."""

    operator: ConditionOperator
    comparator: str | None = None
    path: str | None = None
    value: Any | None = None
    operands: tuple["Condition", ...] = field(default_factory=tuple)

    def evaluate(self, context: Mapping[str, Any]) -> bool:
        """Evaluate the condition against ``context``.

        ``context`` is expected to be a mapping that can resolve the fields
        referenced by the condition.
        """

        if self.operator is ConditionOperator.ALWAYS:
            return True
        if self.operator is ConditionOperator.NEVER:
            return False
        if self.operator is ConditionOperator.NOT:
            if not self.operands:
                raise ValueError("NOT condition requires an operand")
            return not self.operands[0].evaluate(context)
        if self.operator is ConditionOperator.AND:
            if not self.operands:
                raise ValueError("AND condition requires at least one operand")
            return all(op.evaluate(context) for op in self.operands)
        if self.operator is ConditionOperator.OR:
            if not self.operands:
                raise ValueError("OR condition requires at least one operand")
            return any(op.evaluate(context) for op in self.operands)
        if self.operator is ConditionOperator.COMPARISON:
            if self.path is None or self.comparator is None:
                raise ValueError("Comparison condition requires field and comparator")
            comparator = _COMPARATORS.get(self.comparator)
            if comparator is None:
                raise ValueError(f"Unsupported comparator: {self.comparator}")
            lhs = _resolve_field(context, self.path)
            rhs = self.value
            return comparator(lhs, rhs)
        raise ValueError(f"Unsupported operator: {self.operator}")

    @staticmethod
    def always() -> "Condition":
        return Condition(operator=ConditionOperator.ALWAYS)

    @staticmethod
    def never() -> "Condition":
        return Condition(operator=ConditionOperator.NEVER)

    @staticmethod
    def comparison(path: str, comparator: str, value: Any) -> "Condition":
        return Condition(
            operator=ConditionOperator.COMPARISON,
            path=path,
            comparator=comparator,
            value=value,
        )

    @staticmethod
    def logical(operator: ConditionOperator, *operands: "Condition") -> "Condition":
        if operator not in {ConditionOperator.AND, ConditionOperator.OR, ConditionOperator.NOT}:
            raise ValueError("Logical conditions must use AND/OR/NOT operator")
        return Condition(operator=operator, operands=tuple(operands))


def _resolve_field(context: Mapping[str, Any], dotted_path: str) -> Any:
    """Resolve dotted field names against nested mappings."""

    current: Any = context
    for part in dotted_path.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


class EffectPayload(BaseModel):
    """Loose schema for buff effects.

    Effect templates can optionally subclass this model to provide additional
    validation.  By default extra keys are permitted so that legacy payloads
    can be loaded without immediate migration work.
    """

    model_config = ConfigDict(extra="allow")


@dataclass(frozen=True, slots=True)
class Effect:
    """Represents an effect record bound to a buff definition."""

    template_id: str
    parameters: EffectPayload

    def __init__(self, template_id: str, parameters: Mapping[str, Any] | EffectPayload):
        object.__setattr__(self, "template_id", template_id)
        if isinstance(parameters, EffectPayload):
            payload = parameters
        else:
            payload = EffectPayload.model_validate(parameters)
        object.__setattr__(self, "parameters", payload)


@dataclass(frozen=True, slots=True)
class Trigger:
    """Event trigger definition."""

    event_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TargetSelector:
    """Describes how targets should be resolved for a buff."""

    scope: str
    filters: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)


@dataclass(slots=True)
class BuffDefinition:
    """Top level registration entity for a buff."""

    buff_id: str
    name: str
    tags: tuple[str, ...]
    max_stacks: int
    duration: float | None
    stacking_rule: str
    triggers: tuple[Trigger, ...]
    conditions: tuple[Condition, ...]
    effects: tuple[Effect, ...]
    target_selector: TargetSelector
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def iter_triggers(self) -> Iterable[Trigger]:
        return self.triggers

    def iter_effects(self) -> Iterable[Effect]:
        return self.effects

    def to_record(self) -> Mapping[str, Any]:
        """Serialize the definition to a mapping suitable for persistence."""

        return {
            "buff_id": self.buff_id,
            "name": self.name,
            "tags": list(self.tags),
            "max_stacks": self.max_stacks,
            "duration": self.duration,
            "stacking_rule": self.stacking_rule,
            "conditions": [self._condition_to_dict(cond) for cond in self.conditions],
            "target_selector": {
                "scope": self.target_selector.scope,
                "filters": list(self.target_selector.filters),
            },
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def _condition_to_dict(condition: Condition) -> Mapping[str, Any]:
        return {
            "operator": condition.operator.value,
            "comparator": condition.comparator,
            "path": condition.path,
            "value": condition.value,
            "operands": [BuffDefinition._condition_to_dict(op) for op in condition.operands],
        }

    @classmethod
    def from_record(
        cls,
        record: Mapping[str, Any],
        triggers: Sequence[Trigger],
        effects: Sequence[Effect],
    ) -> "BuffDefinition":
        return cls(
            buff_id=str(record["buff_id"]),
            name=str(record.get("name", record["buff_id"])),
            tags=_ensure_tuple(record.get("tags", ())),
            max_stacks=int(record.get("max_stacks", 1)),
            duration=record.get("duration"),
            stacking_rule=str(record.get("stacking_rule", "refresh")),
            triggers=tuple(triggers),
            conditions=tuple(
                _condition_from_dict(raw) for raw in _ensure_sequence(record.get("conditions", ()))
            ),
            effects=tuple(effects),
            target_selector=_selector_from_payload(record.get("target_selector", {})),
            metadata=_ensure_mapping(record.get("metadata", {})),
        )


def _condition_from_dict(payload: Mapping[str, Any]) -> Condition:
    operator = ConditionOperator(str(payload.get("operator", ConditionOperator.ALWAYS.value)))
    operands = tuple(_condition_from_dict(item) for item in payload.get("operands", ()))
    return Condition(
        operator=operator,
        comparator=payload.get("comparator"),
        path=payload.get("path"),
        value=payload.get("value"),
        operands=operands,
    )


def _ensure_sequence(value: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(value, str):
        value = json.loads(value)
    return tuple(value or ())


def _ensure_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = json.loads(value)
    return tuple(value or ())


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    return dict(value or {})


def _selector_from_payload(value: Any) -> TargetSelector:
    if isinstance(value, str):
        value = json.loads(value)
    scope = str((value or {}).get("scope", "self"))
    filters = value.get("filters", ()) if isinstance(value, Mapping) else ()
    if isinstance(filters, str):
        filters = json.loads(filters)
    return TargetSelector(scope=scope, filters=tuple(filters or ()))
