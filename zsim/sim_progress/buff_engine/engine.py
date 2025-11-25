"""Runtime services that operate on the buff registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence

from .definitions import BuffDefinition, Condition, Effect
from .registry import BuffRegistry
from .store import BuffStore

EffectHandler = Callable[[Effect, BuffDefinition, "BuffExecutionContext"], Any]


@dataclass(slots=True)
class BuffExecutionContext:
    """Container passed to effect handlers during dispatch."""

    event: Mapping[str, Any]
    actor: Any | None = None
    targets: Sequence[Any] = field(default_factory=tuple)
    store: BuffStore | None = None
    extra: MutableMapping[str, Any] = field(default_factory=dict)

    def as_mapping(self) -> Mapping[str, Any]:
        mapping: dict[str, Any] = dict(self.extra)
        mapping.setdefault("event", self.event)
        mapping.setdefault("actor", self.actor)
        mapping.setdefault("targets", self.targets)
        mapping.setdefault("store", self.store)
        return mapping


class EventRouter:
    """Index based dispatcher that maps events to candidate buffs."""

    def __init__(self, registry: BuffRegistry) -> None:
        self._registry = registry
        self._cache: dict[str, tuple[str, ...]] = {}
        self._dirty = True

    def invalidate(self) -> None:
        self._dirty = True

    def _ensure_cache(self) -> None:
        if self._dirty:
            self._cache = dict(self._registry.as_event_index())
            self._dirty = False

    def route(self, event_type: str) -> tuple[str, ...]:
        self._ensure_cache()
        return self._cache.get(event_type, ())


class ConditionEvaluator:
    """Applies condition trees for a buff against a runtime context."""

    def matches(self, definition: BuffDefinition, context: BuffExecutionContext) -> bool:
        if not definition.conditions:
            return True
        mapping = context.as_mapping()
        return all(
            self._evaluate_condition(condition, mapping) for condition in definition.conditions
        )

    def _evaluate_condition(self, condition: Condition, mapping: Mapping[str, Any]) -> bool:
        return condition.evaluate(mapping)


class EffectExecutor:
    """Resolves effect templates and executes them."""

    def __init__(self, handlers: Mapping[str, EffectHandler] | None = None) -> None:
        self._handlers: dict[str, EffectHandler] = dict(handlers or {})

    def register_handler(self, template_id: str, handler: EffectHandler) -> None:
        self._handlers[template_id] = handler

    def execute(self, definition: BuffDefinition, context: BuffExecutionContext) -> list[Any]:
        results: list[Any] = []
        for effect in definition.effects:
            handler = self._handlers.get(effect.template_id)
            if handler is None:
                raise KeyError(f"Effect handler not registered for template {effect.template_id}")
            results.append(handler(effect, definition, context))
        return results


class BuffEngine:
    """Facade that wires the registry and runtime services together."""

    def __init__(
        self,
        registry: BuffRegistry,
        router: EventRouter | None = None,
        evaluator: ConditionEvaluator | None = None,
        executor: EffectExecutor | None = None,
    ) -> None:
        self.registry = registry
        self.router = router or EventRouter(registry)
        self.evaluator = evaluator or ConditionEvaluator()
        self.executor = executor or EffectExecutor()

    def register_definition(self, definition: BuffDefinition) -> None:
        self.registry.register_definition(definition)
        self.router.invalidate()

    def dispatch(
        self, event_type: str, context: BuffExecutionContext
    ) -> list[tuple[str, list[Any]]]:
        """Dispatch an event and execute matched buff effects.

        Returns a list of tuples ``(buff_id, effect_results)`` representing the
        buffs whose conditions matched and were executed.
        """

        executed: list[tuple[str, list[Any]]] = []
        for buff_id in self.router.route(event_type):
            definition = self.registry.get_definition(buff_id)
            if not self.evaluator.matches(definition, context):
                continue
            results = self.executor.execute(definition, context)
            executed.append((buff_id, results))
        return executed

    def refresh_router(self) -> None:
        self.router.invalidate()

    def iter_buffs_for_event(self, event_type: str) -> Iterable[BuffDefinition]:
        for buff_id in self.router.route(event_type):
            yield self.registry.get_definition(buff_id)
