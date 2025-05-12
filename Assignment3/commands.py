
from dataclasses import dataclass

__all__ = [
    "Command",
    "PlaceOrder",
    "CancelOrder",
    "DebitFunds",
    "CreditFunds",
    "ExecuteTrade"
]


class Command:
    pass

@dataclass(slots=True)
class ExecuteTrade(Command):
    buy_order_id: str
    sell_order_id: str
    symbol: str
    quantity: int
    price: float

@dataclass(slots=True)
class PlaceOrder(Command):
    user_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    price: float


@dataclass(slots=True)
class CancelOrder(Command):
    order_id: str
    user_id: str


@dataclass(slots=True)
class DebitFunds(Command):
    user_id: str
    amount: float


@dataclass(slots=True)
class CreditFunds(Command):
    user_id: str
    amount: float
