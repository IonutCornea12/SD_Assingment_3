
import uuid
from commands import (
    PlaceOrder,
    CancelOrder,
    DebitFunds,
    CreditFunds,
    ExecuteTrade,
    Command,
)
from models import Side
from aggregates import OrderBook, Account
from event_store import InMemoryEventStore
from repository import Repository

class CommandDispatcher:
    def __init__(self, store: InMemoryEventStore) -> None:
        self._store = store
        self._order_repo = Repository(store, OrderBook)
        self._account_repo = Repository(store, Account)

    def handle(self, cmd: Command) -> None:
        handler = {
            PlaceOrder: self._handle_place_order,
            CancelOrder: self._handle_cancel_order,
            DebitFunds: self._handle_debit_funds,
            CreditFunds: self._handle_credit_funds,
            ExecuteTrade: self._handle_execute_trade,

        }[type(cmd)]
        handler(cmd)

    def _handle_place_order(self, cmd: PlaceOrder) -> None:
        # ensure account has enough funds for BUY side
        acct = self._account_repo.get(cmd.user_id)
        if cmd.side.upper() == "BUY" and acct.balance < cmd.quantity * cmd.price:
            raise ValueError("Insufficient funds to place order")

        # get or create order book
        ob = self._order_repo.get(cmd.symbol)
        if ob._version == 0:
            ob = OrderBook.create(cmd.symbol)

        order_id = str(uuid.uuid4())
        ob.place_order(order_id, cmd.user_id, Side(cmd.side.upper()), cmd.quantity, cmd.price)

        self._order_repo.save(ob)
    #scan every orderbook
    def _handle_cancel_order(self, cmd: CancelOrder) -> None:
        for symbol in {evt.symbol for evt in self._store.get_all_events() if hasattr(evt, "symbol")}:
            ob = self._order_repo.get(symbol)
            if cmd.order_id in ob.orders:
                ob.cancel_order(cmd.order_id, cmd.user_id)
                self._order_repo.save(ob)
                return
        raise KeyError("Order id not found")

    def _handle_debit_funds(self, cmd: DebitFunds) -> None:
        acct = self._account_repo.get(cmd.user_id)
        if acct._version == 0:
            acct = Account.create(cmd.user_id)
        acct.debit(cmd.amount)
        self._account_repo.save(acct)

    def _handle_credit_funds(self, cmd: CreditFunds) -> None:
        acct = self._account_repo.get(cmd.user_id)
        if acct._version == 0:
            acct = Account.create(cmd.user_id)
        acct.credit(cmd.amount)
        self._account_repo.save(acct)

    def _handle_execute_trade(self, cmd: ExecuteTrade) -> None:
        ob = self._order_repo.get(cmd.symbol)
        ob.execute_trade(
            buy_id=cmd.buy_order_id,
            sell_id=cmd.sell_order_id,
            qty=cmd.quantity,
            price=cmd.price
        )
        self._order_repo.save(ob)