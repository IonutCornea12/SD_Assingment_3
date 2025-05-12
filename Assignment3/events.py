
import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Any, Dict

__all__ = [
    "DomainEvent",
    "OrderPlaced",
    "OrderCancelled",
    "TradeExecuted",
    "FundsDebited",
    "FundsCredited",
]


@dataclass(frozen=True, slots=True)
class DomainEvent:
    id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)
    occurred_on: datetime = field(default_factory=datetime.utcnow, init=False)

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "id": str(self.id),
            "occurred_on": self.occurred_on.isoformat(),
            "type": self.__class__.__name__,
        }
        dynamic_fields = {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if f.name not in {"id", "occurred_on"}
        }
        return {**base, **dynamic_fields}


@dataclass(frozen=True, slots=True)
class OrderPlaced(DomainEvent):
    order_id: str
    user_id: str
    symbol: str
    side: str  # "BUY" | "SELL"
    quantity: int
    price: float


@dataclass(frozen=True, slots=True)
class OrderCancelled(DomainEvent):
    order_id: str
    user_id: str
    symbol: str


@dataclass(frozen=True, slots=True)
class TradeExecuted(DomainEvent):
    buy_order_id: str
    sell_order_id: str
    symbol: str
    quantity: int
    price: float


@dataclass(frozen=True, slots=True)
class FundsDebited(DomainEvent):
    user_id: str
    amount: float


@dataclass(frozen=True, slots=True)
class FundsCredited(DomainEvent):
    user_id: str
    amount: float