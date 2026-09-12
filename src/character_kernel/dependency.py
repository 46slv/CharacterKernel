from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class FreshnessReport:
    status: str
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]

    @property
    def is_fresh(self) -> bool:
        return self.status == "VALID"


def check_freshness(
    expected_sources: Mapping[str, str],
    current_sources: Mapping[str, str],
) -> FreshnessReport:
    missing = tuple(sorted(key for key in expected_sources if key not in current_sources))
    mismatched = tuple(
        sorted(
            key
            for key, expected in expected_sources.items()
            if key in current_sources and current_sources[key] != expected
        )
    )
    status = "VALID" if not missing and not mismatched else "REBIND_REQUIRED"
    return FreshnessReport(status=status, missing=missing, mismatched=mismatched)


class DependencyGraph:
    """Directed source -> derived dependency graph with deterministic closure."""

    def __init__(self, edges: Mapping[str, Iterable[str]] | None = None) -> None:
        self._edges: dict[str, set[str]] = {}
        if edges:
            for source, derived in edges.items():
                self._edges[source] = set(derived)

    def add(self, source: str, derived: str) -> None:
        if not source or not derived:
            raise ValueError("dependency node ids must be non-empty")
        self._edges.setdefault(source, set()).add(derived)

    def closure(self, changed_sources: Iterable[str]) -> tuple[str, ...]:
        queue = sorted(set(changed_sources))
        visited: set[str] = set(queue)
        derived: set[str] = set()

        while queue:
            current = queue.pop(0)
            for target in sorted(self._edges.get(current, ())):
                if target in visited:
                    continue
                visited.add(target)
                derived.add(target)
                queue.append(target)
        return tuple(sorted(derived))
