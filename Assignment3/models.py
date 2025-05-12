
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
#represents direction of trade
__all__ = ["Side", "Order"]

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(slots=True)
class Order:
    order_id: str
    user_id: str
    symbol: str
    side: Side
    quantity: int
    price: float
    status: str = "OPEN"
