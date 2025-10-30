"""SQLite backed registry for buff definitions."""

from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
import json
import sqlite3
from typing import Iterable, Iterator, Mapping, Sequence

from .definitions import (
    BuffDefinition,
    Condition,
    Effect,
    EffectPayload,
    TargetSelector,
    Trigger,
    _condition_from_dict,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS buffs (
    buff_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tags TEXT NOT NULL,
    max_stacks INTEGER NOT NULL,
    duration REAL,
    stacking_rule TEXT NOT NULL,
    conditions TEXT NOT NULL,
    target_selector TEXT NOT NULL,
    metadata TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS buff_triggers (
    buff_id TEXT NOT NULL,
    trigger_order INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    parameters TEXT NOT NULL,
    PRIMARY KEY (buff_id, trigger_order),
    FOREIGN KEY (buff_id) REFERENCES buffs(buff_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS buff_effects (
    buff_id TEXT NOT NULL,
    effect_order INTEGER NOT NULL,
    template_id TEXT NOT NULL,
    parameters TEXT NOT NULL,
    PRIMARY KEY (buff_id, effect_order),
    FOREIGN KEY (buff_id) REFERENCES buffs(buff_id) ON DELETE CASCADE
);
"""


class BuffRegistry(AbstractContextManager):
    """Persisted registry for the modern buff system."""

    def __init__(self, database: str | Path | None = None) -> None:
        self._path = str(database or ":memory:")
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:  # auto commit
            self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # Context manager support -------------------------------------------------
    def __enter__(self) -> "BuffRegistry":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # CRUD -------------------------------------------------------------------
    def register_definition(self, definition: BuffDefinition) -> None:
        record = definition.to_record()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO buffs (buff_id, name, tags, max_stacks, duration, stacking_rule, conditions, target_selector, metadata)
                VALUES (:buff_id, :name, :tags, :max_stacks, :duration, :stacking_rule, :conditions, :target_selector, :metadata)
                ON CONFLICT(buff_id) DO UPDATE SET
                    name = excluded.name,
                    tags = excluded.tags,
                    max_stacks = excluded.max_stacks,
                    duration = excluded.duration,
                    stacking_rule = excluded.stacking_rule,
                    conditions = excluded.conditions,
                    target_selector = excluded.target_selector,
                    metadata = excluded.metadata
                """,
                {
                    "buff_id": definition.buff_id,
                    "name": record["name"],
                    "tags": json.dumps(record["tags"], ensure_ascii=False),
                    "max_stacks": record["max_stacks"],
                    "duration": record["duration"],
                    "stacking_rule": record["stacking_rule"],
                    "conditions": json.dumps(record["conditions"], ensure_ascii=False),
                    "target_selector": json.dumps(record["target_selector"], ensure_ascii=False),
                    "metadata": json.dumps(record["metadata"], ensure_ascii=False),
                },
            )
            self._conn.execute(
                "DELETE FROM buff_triggers WHERE buff_id = ?",
                (definition.buff_id,),
            )
            trigger_rows = [
                (
                    definition.buff_id,
                    index,
                    trigger.event_type,
                    json.dumps(trigger.parameters, ensure_ascii=False),
                )
                for index, trigger in enumerate(definition.triggers)
            ]
            if trigger_rows:
                self._conn.executemany(
                    "INSERT INTO buff_triggers (buff_id, trigger_order, event_type, parameters) VALUES (?, ?, ?, ?)",
                    trigger_rows,
                )
            self._conn.execute(
                "DELETE FROM buff_effects WHERE buff_id = ?",
                (definition.buff_id,),
            )
            effect_rows = [
                (
                    definition.buff_id,
                    index,
                    effect.template_id,
                    json.dumps(effect.parameters.model_dump(), ensure_ascii=False),
                )
                for index, effect in enumerate(definition.effects)
            ]
            if effect_rows:
                self._conn.executemany(
                    "INSERT INTO buff_effects (buff_id, effect_order, template_id, parameters) VALUES (?, ?, ?, ?)",
                    effect_rows,
                )

    def get_definition(self, buff_id: str) -> BuffDefinition:
        cursor = self._conn.cursor()
        row = cursor.execute("SELECT * FROM buffs WHERE buff_id = ?", (buff_id,)).fetchone()
        if row is None:
            raise KeyError(buff_id)
        triggers = self._load_triggers_for_buff(buff_id)
        effects = self._load_effects_for_buff(buff_id)
        return BuffDefinition.from_record(dict(row), triggers=triggers, effects=effects)

    def iter_definitions(self) -> Iterator[BuffDefinition]:
        cursor = self._conn.cursor()
        for row in cursor.execute("SELECT * FROM buffs ORDER BY buff_id"):
            buff_id = row["buff_id"]
            triggers = self._load_triggers_for_buff(buff_id)
            effects = self._load_effects_for_buff(buff_id)
            yield BuffDefinition.from_record(dict(row), triggers=triggers, effects=effects)

    def list_triggers_for_event(self, event_type: str) -> Sequence[tuple[str, Trigger]]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            """
            SELECT buff_id, trigger_order, event_type, parameters
            FROM buff_triggers
            WHERE event_type = ?
            ORDER BY trigger_order
            """,
            (event_type,),
        ).fetchall()
        result: list[tuple[str, Trigger]] = []
        for row in rows:
            trigger = Trigger(
                event_type=row["event_type"], parameters=json.loads(row["parameters"])
            )
            result.append((row["buff_id"], trigger))
        return result

    def _load_triggers_for_buff(self, buff_id: str) -> Sequence[Trigger]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            "SELECT event_type, parameters FROM buff_triggers WHERE buff_id = ? ORDER BY trigger_order",
            (buff_id,),
        ).fetchall()
        return tuple(
            Trigger(event_type=row["event_type"], parameters=json.loads(row["parameters"]))
            for row in rows
        )

    def _load_effects_for_buff(self, buff_id: str) -> Sequence[Effect]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            "SELECT template_id, parameters FROM buff_effects WHERE buff_id = ? ORDER BY effect_order",
            (buff_id,),
        ).fetchall()
        return tuple(
            Effect(
                template_id=row["template_id"],
                parameters=EffectPayload.model_validate_json(row["parameters"]),
            )
            for row in rows
        )

    def delete(self, buff_id: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM buffs WHERE buff_id = ?", (buff_id,))

    def clear(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM buff_triggers")
            self._conn.execute("DELETE FROM buff_effects")
            self._conn.execute("DELETE FROM buffs")

    def load_target_selector(self, buff_id: str) -> TargetSelector:
        row = self._conn.execute(
            "SELECT target_selector FROM buffs WHERE buff_id = ?",
            (buff_id,),
        ).fetchone()
        if row is None:
            raise KeyError(buff_id)
        payload = json.loads(row["target_selector"])
        return TargetSelector(scope=payload["scope"], filters=tuple(payload.get("filters", ())))

    def load_conditions(self, buff_id: str) -> Sequence[Condition]:
        row = self._conn.execute(
            "SELECT conditions FROM buffs WHERE buff_id = ?",
            (buff_id,),
        ).fetchone()
        if row is None:
            raise KeyError(buff_id)
        payload = json.loads(row["conditions"])
        return tuple(_condition_from_dict(item) for item in payload)

    # Utility ----------------------------------------------------------------
    def count(self) -> int:
        cursor = self._conn.cursor()
        row = cursor.execute("SELECT COUNT(*) AS total FROM buffs").fetchone()
        return int(row["total"]) if row else 0

    def as_event_index(self) -> Mapping[str, tuple[str, ...]]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            "SELECT DISTINCT event_type, buff_id FROM buff_triggers ORDER BY event_type, buff_id"
        ).fetchall()
        event_map: dict[str, list[str]] = {}
        for row in rows:
            event_map.setdefault(row["event_type"], []).append(row["buff_id"])
        return {key: tuple(value) for key, value in event_map.items()}

    def iter_effects(self, buff_id: str) -> Iterable[Effect]:
        return self._load_effects_for_buff(buff_id)

    def iter_triggers(self, buff_id: str) -> Iterable[Trigger]:
        return self._load_triggers_for_buff(buff_id)
