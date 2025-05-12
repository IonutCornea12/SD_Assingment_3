from pprint import pprint
from event_store import InMemoryEventStore
from handlers import CommandDispatcher
from commands import (
    PlaceOrder, CancelOrder, ExecuteTrade,
    DebitFunds, CreditFunds,
)
from aggregates import OrderBook, Account
import uuid
from repository import  Repository


def run_scenario():
    store = InMemoryEventStore()
    handler = CommandDispatcher(store)

    # U1 deposits $10,000 and places a BUY order
    handler.handle(CreditFunds(user_id="U1", amount=10_000))
    handler.handle(PlaceOrder(user_id="U1", symbol="AAPL", side="BUY", quantity=50, price=100.00))

    # U2 deposits 0 and places a SELL order
    handler.handle(CreditFunds(user_id="U2", amount=0))
    handler.handle(PlaceOrder(user_id="U2", symbol="AAPL", side="SELL", quantity=50, price=100.00))

    # Fetch the generated order ids from event log
    all_events = store.get_all_events()
    buy_order = next(e for e in all_events if getattr(e, "side", "") == "BUY")
    sell_order = next(e for e in all_events if getattr(e, "side", "") == "SELL")

    # Match the trade
    handler.handle(ExecuteTrade(
        buy_order_id=buy_order.order_id,
        sell_order_id=sell_order.order_id,
        symbol="AAPL",
        quantity=50,
        price=190.00,
    ))

    # U1 pays, U2 receives
    handler.handle(DebitFunds(user_id="U1", amount=50 * 190.00))
    handler.handle(CreditFunds(user_id="U2", amount=50 * 190.00))

    return store


def replay_with_repo(store):
    account_repo = Repository(store, Account)
    order_repo = Repository(store, OrderBook)

    # Replay order book
    order_book = order_repo.get("AAPL")

    # Replay accounts
    user_accounts = {}
    for evt in store.get_all_events():
        if hasattr(evt, "user_id"):
            uid = evt.user_id
            if uid not in user_accounts:
                user_accounts[uid] = account_repo.get(uid)

    return order_book, user_accounts

if __name__ == "__main__":
    store = run_scenario()

    print("\nEvent log:")
    for e in store.get_all_events():
        pprint(e.to_dict())

    order_book, ledger = replay_with_repo(store)

    print("\nReplayed order books:")
    for sym in ["AAPL"]:
        print(sym, {k: v.__dict__ for k, v in order_book.orders.items() if v.symbol == sym})

    print("\nReplayed account balances:")
    for user_id, account in ledger.items():
        print(user_id, account.balance)