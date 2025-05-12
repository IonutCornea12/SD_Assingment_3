from typing import Type, TypeVar

from event_store import InMemoryEventStore
from events import (
    DomainEvent,
    OrderPlaced,
    OrderCancelled,
    TradeExecuted,
    FundsDebited,
    FundsCredited,
)
from aggregates import AggregateRoot

T = TypeVar("T", bound=AggregateRoot)

class Repository:
    def __init__(self, store: InMemoryEventStore, aggregate_cls: Type[T]):
        self._store = store
        self._cls = aggregate_cls

    def get(self, aggregate_id: str) -> T:
        agg = self._cls(aggregate_id)
        for evt in self._store.get_all_events():
            if self._is_relevant(aggregate_id, evt):
                agg._apply(evt)
        return agg

    def save(self, aggregate: T) -> None:
        for evt in aggregate.pull_events():
            self._store.append(evt)

    def _is_relevant(self, agg_id: str, evt: DomainEvent) -> bool:
        if isinstance(evt, (OrderPlaced, OrderCancelled, TradeExecuted)):
            return getattr(evt, "symbol", None) == agg_id
        if isinstance(evt, (FundsDebited, FundsCredited)):
            return getattr(evt, "user_id", None) == agg_id
        return False
