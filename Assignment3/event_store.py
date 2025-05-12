from typing import List
from events import DomainEvent

__all__ = ["InMemoryEventStore"]

class InMemoryEventStore:

    def __init__(self):
        self._events: List[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    def get_all_events(self) -> List[DomainEvent]:
        return list(self._events)