
from typing import List, Dict
from events import (
    DomainEvent,
    OrderPlaced,
    OrderCancelled,
    TradeExecuted,
    FundsDebited,
    FundsCredited,
)
from models import Order, Side

__all__ = ["AggregateRoot", "OrderBook", "Account"]

class AggregateRoot:
    def __init__(self, aggregate_id: str):
        self.id: str = aggregate_id
        self._version: int = 0
        self._pending: list[DomainEvent] = []

    def _record(self, event: DomainEvent) -> None:
        self._pending.append(event)
        self._apply(event)

    def _apply(self, event: DomainEvent) -> None:
        handler = getattr(self, f"_apply_{event.__class__.__name__}", None)
        if handler:
            handler(event)
        self._version += 1

    def pull_events(self) -> List[DomainEvent]:
        out = self._pending[:]
        self._pending.clear()
        return out

class OrderBook(AggregateRoot):
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.symbol = symbol
        self.orders: Dict[str, Order] = {}

    @classmethod
    def create(cls, symbol: str) -> "OrderBook":
        return cls(symbol)

    def place_order(self, order_id: str, user_id: str, side: Side, qty: int, price: float) -> None:
        self._record(OrderPlaced(
            order_id=order_id,
            user_id=user_id,
            symbol=self.symbol,
            side=side.value,
            quantity=qty,
            price=price,
        ))

    def cancel_order(self, order_id: str, user_id: str) -> None:
        if order_id not in self.orders:
            raise KeyError(f"No such order {order_id}")
        self._record(OrderCancelled(order_id=order_id, user_id=user_id, symbol=self.symbol))
    def execute_trade(self, buy_id: str, sell_id: str, qty: int, price: float) -> None:
        if buy_id not in self.orders or sell_id not in self.orders:
            raise KeyError("Order ids missing for trade")
        self._record(TradeExecuted(
            buy_order_id=buy_id,
            sell_order_id=sell_id,
            symbol=self.symbol,
            quantity=qty,
            price=price,
        ))

    def _apply_OrderPlaced(self, e: OrderPlaced) -> None:
        self.orders[e.order_id] = Order(
            order_id=e.order_id,
            user_id=e.user_id,
            symbol=e.symbol,
            side=Side(e.side),
            quantity=e.quantity,
            price=e.price,
        )

    def _apply_OrderCancelled(self, e: OrderCancelled) -> None:
        if e.order_id in self.orders:
            del self.orders[e.order_id]

    def _apply_TradeExecuted(self, e: TradeExecuted) -> None:
        # mark both orders filled & remove
        for oid in (e.buy_order_id, e.sell_order_id):
            if oid in self.orders:
                self.orders[oid].status = "FILLED"
                del self.orders[oid]

class Account(AggregateRoot):
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.user_id = user_id
        self.balance: float = 0.0

    @classmethod
    def create(cls, user_id: str) -> "Account":
        return cls(user_id)

    def debit(self, amount: float) -> None:
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self._record(FundsDebited(user_id=self.user_id, amount=amount))

    def credit(self, amount: float) -> None:
        self._record(FundsCredited(user_id=self.user_id, amount=amount))

    def _apply_FundsDebited(self, e: FundsDebited) -> None:
        self.balance -= e.amount

    def _apply_FundsCredited(self, e: FundsCredited) -> None:
        self.balance += e.amount