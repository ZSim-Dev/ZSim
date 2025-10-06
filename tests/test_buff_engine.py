from __future__ import annotations

from dataclasses import dataclass

import pytest

from zsim.sim_progress.buff_engine import (
    BuffDefinition,
    BuffEngine,
    BuffExecutionContext,
    BuffInstance,
    BuffRegistry,
    BuffStore,
    Condition,
    ConditionEvaluator,
    ConditionOperator,
    Effect,
    EffectExecutor,
    EventRouter,
    TargetSelector,
    Trigger,
)


@dataclass
class DummyEvent:
    type: str
    payload: dict[str, int]


@dataclass
class DummyActor:
    name: str
    level: int


def build_definition() -> BuffDefinition:
    return BuffDefinition(
        buff_id="buff.test",
        name="Test Buff",
        tags=("test",),
        max_stacks=3,
        duration=10.0,
        stacking_rule="refresh",
        triggers=(Trigger(event_type="skill.cast", parameters={"skill": "E"}),),
        conditions=(
            Condition.logical(
                ConditionOperator.AND,
                Condition.comparison("event.type", "==", "skill.cast"),
                Condition.logical(
                    ConditionOperator.OR,
                    Condition.comparison("actor.level", ">=", 10),
                    Condition.comparison("event.payload.combo", ">=", 3),
                ),
            ),
        ),
        effects=(Effect("add.atk", {"value": 120}),),
        target_selector=TargetSelector(scope="self", filters=({"type": "ally"},)),
        metadata={"category": "unit"},
    )


def test_condition_evaluator_handles_nested_logic() -> None:
    definition = build_definition()
    evaluator = ConditionEvaluator()
    context = BuffExecutionContext(
        event={"type": "skill.cast", "payload": {"combo": 4}},
        actor=DummyActor(name="Hero", level=5),
    )
    assert evaluator.matches(definition, context)

    failing_context = BuffExecutionContext(
        event={"type": "skill.cast", "payload": {"combo": 1}},
        actor=DummyActor(name="Hero", level=5),
    )
    assert not evaluator.matches(definition, failing_context)


def test_registry_round_trip() -> None:
    definition = build_definition()
    with BuffRegistry() as registry:
        registry.register_definition(definition)
        loaded = registry.get_definition(definition.buff_id)

    assert loaded.buff_id == definition.buff_id
    assert loaded.name == definition.name
    assert loaded.triggers[0].event_type == "skill.cast"
    assert loaded.effects[0].template_id == "add.atk"
    assert loaded.target_selector.scope == "self"


def test_event_router_and_engine_dispatch() -> None:
    definition = build_definition()
    registry = BuffRegistry()
    engine = BuffEngine(
        registry=registry,
        router=EventRouter(registry),
        evaluator=ConditionEvaluator(),
        executor=EffectExecutor(),
    )
    results: list[tuple[str, int]] = []

    def handler(effect: Effect, buff: BuffDefinition, context: BuffExecutionContext) -> int:
        value = effect.parameters.model_dump()["value"]
        results.append((buff.buff_id, value))
        return value

    engine.executor.register_handler("add.atk", handler)
    engine.register_definition(definition)

    context = BuffExecutionContext(
        event={"type": "skill.cast", "payload": {"combo": 5}},
        actor=DummyActor(name="Hero", level=20),
    )

    dispatch_results = engine.dispatch("skill.cast", context)
    assert dispatch_results == [(definition.buff_id, [120])]
    assert results == [(definition.buff_id, 120)]


def test_buff_store_operations() -> None:
    store = BuffStore()
    instance = BuffInstance(buff_id="buff.test", owner_id="hero", remaining_duration=1.0)
    store.add(instance)
    assert store.get("hero") == (instance,)

    store.tick_all(0.5)
    assert pytest.approx(store.get("hero")[0].remaining_duration, rel=1e-6) == 0.5

    removed = store.purge_expired()
    assert removed == 0

    store.tick_all(0.5)
    assert store.get("hero")[0].expired
    removed = store.purge_expired()
    assert removed == 1
    assert store.get("hero") == ()
