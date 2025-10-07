"""Runtime storage abstraction for active buff instances."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, MutableMapping


@dataclass(slots=True)
class BuffInstance:
    """Light-weight runtime state for a buff."""

    buff_id: str
    owner_id: str
    stacks: int = 1
    remaining_duration: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def tick(self, delta: float) -> None:
        if self.remaining_duration is None:
            return
        self.remaining_duration = max(0.0, self.remaining_duration - delta)

    @property
    def expired(self) -> bool:
        return self.remaining_duration is not None and self.remaining_duration <= 0


class BuffStore:
    """Encapsulates CRUD operations on the dynamic buff dictionary."""

    def __init__(
        self, backing_store: MutableMapping[str, list[BuffInstance]] | None = None
    ) -> None:
        self._store: MutableMapping[str, list[BuffInstance]]
        if backing_store is None:
            self._store = defaultdict(list)
            self._owns_store = True
        else:
            self._store = backing_store
            self._owns_store = False

    def add(self, instance: BuffInstance) -> None:
        self._store.setdefault(instance.owner_id, []).append(instance)

    def remove(self, owner_id: str, predicate: Callable[[BuffInstance], bool]) -> int:
        instances = self._store.get(owner_id, [])
        kept: list[BuffInstance] = []
        removed = 0
        for inst in instances:
            if predicate(inst):
                removed += 1
            else:
                kept.append(inst)
        if kept:
            self._store[owner_id] = kept
        else:
            self._store.pop(owner_id, None)
        return removed

    def get(self, owner_id: str) -> tuple[BuffInstance, ...]:
        return tuple(self._store.get(owner_id, ()))

    def find(self, owner_id: str, buff_id: str) -> tuple[BuffInstance, ...]:
        return tuple(inst for inst in self._store.get(owner_id, ()) if inst.buff_id == buff_id)

    def tick_all(self, delta: float) -> None:
        for instances in list(self._store.values()):
            for inst in instances:
                inst.tick(delta)

    def purge_expired(self) -> int:
        removed = 0
        for owner_id in list(self._store.keys()):
            removed += self.remove(owner_id, lambda inst: inst.expired)
        return removed

    def clear(self) -> None:
        self._store.clear()

    def iter_all(self) -> Iterator[tuple[str, BuffInstance]]:
        for owner_id, instances in self._store.items():
            for inst in instances:
                yield owner_id, inst

    def as_dict(self) -> MutableMapping[str, list[BuffInstance]]:
        return self._store

    def owns_store(self) -> bool:
        return self._owns_store

    def sync_from(self, source: MutableMapping[str, list[BuffInstance]]) -> None:
        self._store.clear()
        for owner_id, instances in source.items():
            self._store[owner_id] = list(instances)
