"""Local TWS paper-trading CLI. Order submission is always explicit."""

import argparse
from decimal import Decimal, InvalidOperation
import json
import math
import sys

from ib_async import IB, LimitOrder, Stock


def positive_number(value):
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("Enter a positive number") from exc
    if not number.is_finite() or number <= 0 or not math.isfinite(float(number)):
        raise argparse.ArgumentTypeError("Enter a finite positive number")
    return float(number)


def paper_account(accounts, requested=None):
    # Fail closed: this first version supports only standard DU paper accounts.
    if not accounts or any(not a.startswith("DU") for a in accounts):
        raise ValueError("Expected only DU paper accounts; refusing this session")
    if requested:
        if requested not in accounts:
            raise ValueError("Requested account is not in this TWS session")
        return requested
    if len(accounts) != 1:
        raise ValueError("Multiple accounts available; choose one with --account")
    return accounts[0]


def trade_info(trade):
    return {
        "order_id": trade.order.orderId,
        "client_id": trade.order.clientId,
        "account": trade.order.account,
        "symbol": trade.contract.symbol,
        "action": trade.order.action,
        "quantity": trade.order.totalQuantity,
        "limit_price": trade.order.lmtPrice,
        "status": trade.orderStatus.status,
        "filled": trade.orderStatus.filled,
        "remaining": trade.orderStatus.remaining,
        "messages": [entry.message for entry in trade.log if entry.message],
    }


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497)
    p.add_argument("--client-id", type=int, default=17)
    p.add_argument("--account", help="Select a DU paper account")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("account", help="Read account summary and positions")
    sub.add_parser("orders", help="Read open orders across API clients")
    order = sub.add_parser("order", help="Preview a stock limit order; --submit sends it")
    order.add_argument("symbol")
    order.add_argument("action", choices=["BUY", "SELL"])
    order.add_argument("quantity", type=positive_number)
    order.add_argument("limit_price", type=positive_number)
    order.add_argument("--currency", default="USD")
    order.add_argument("--submit", action="store_true")
    cancel = sub.add_parser("cancel", help="Cancel an open order owned by this client ID")
    cancel.add_argument("order_id", type=int)
    cancel.add_argument("--submit", action="store_true")
    return p


def run(args):
    ib = IB()
    ib.RequestTimeout = 20
    ib.RaiseRequestErrors = True
    modifying = args.command in {"order", "cancel"} and args.submit
    try:
        ib.connect(args.host, args.port, clientId=args.client_id,
                   timeout=10, readonly=not modifying)
        account = paper_account(ib.managedAccounts(), args.account)
        if args.command == "account":
            print(json.dumps({
                "account": account,
                "summary": [v._asdict() for v in ib.accountSummary(account)],
                "positions": [{"symbol": p.contract.symbol, "quantity": p.position,
                               "average_cost": p.avgCost}
                              for p in ib.positions(account)],
            }, indent=2, default=str))
        elif args.command == "orders":
            print(json.dumps([trade_info(t) for t in ib.reqAllOpenOrders()
                              if t.order.account == account], indent=2, default=str))
        elif args.command == "order":
            contracts = ib.qualifyContracts(Stock(args.symbol.upper(), "SMART", args.currency))
            if len(contracts) != 1:
                raise ValueError("Stock contract could not be uniquely qualified")
            contract = contracts[0]
            order = LimitOrder(args.action, args.quantity, args.limit_price,
                               account=account, tif="DAY", outsideRth=False)
            print(json.dumps({"mode": "SUBMIT" if args.submit else "PREVIEW ONLY",
                              "account": account, "contract_id": contract.conId,
                              "symbol": contract.symbol, "action": args.action,
                              "quantity": args.quantity, "limit_price": args.limit_price,
                              "currency": args.currency, "time_in_force": "DAY",
                              "outside_regular_hours": False}, indent=2))
            if not args.submit:
                return 0
            trade = ib.placeOrder(contract, order)
            # A submitted order may stay open after this process disconnects.
            for _ in range(100):
                ib.sleep(0.1)
                if trade.orderStatus.status in {"Submitted", "Filled", "Cancelled", "Inactive"}:
                    break
            print(json.dumps(trade_info(trade), indent=2, default=str))
            if trade.orderStatus.status in {"Cancelled", "Inactive"}:
                return 1
            if trade.orderStatus.status != "Filled":
                print("Order may remain open. Check TWS or run orders; submission is not a fill.",
                      file=sys.stderr)
        elif args.command == "cancel":
            trades = ib.reqOpenOrders()
            matches = [t for t in trades if t.order.orderId == args.order_id
                       and t.order.clientId == args.client_id and t.order.account == account]
            if len(matches) != 1:
                raise ValueError("No matching open order owned by this account/client ID")
            trade = matches[0]
            if not args.submit:
                print("PREVIEW ONLY: rerun with --submit to request cancellation")
                print(json.dumps(trade_info(trade), indent=2, default=str))
                return 0
            ib.cancelOrder(trade.order)
            for _ in range(100):
                ib.sleep(0.1)
                if trade.isDone():
                    break
            print(json.dumps(trade_info(trade), indent=2, default=str))
            if trade.orderStatus.status != "Cancelled":
                print("Cancellation not confirmed. Check TWS before retrying.", file=sys.stderr)
                return 1
        return 0
    finally:
        ib.disconnect()


def main():
    args = parser().parse_args()
    try:
        return run(args)
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print(f"Error: {exc or type(exc).__name__}. Check TWS login, API settings, port and client ID.",
              file=sys.stderr)
        print("If submitting an order, check TWS before retrying: connection loss does not prove rejection.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
