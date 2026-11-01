"""Read-only IBKR historical download and next-bar SPY SMA crossover backtest."""

import argparse
import calendar
import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import json
import math
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def six_months_before(day):
    month = day.month - 6
    year = day.year
    if month <= 0:
        month += 12
        year -= 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def parse_timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Bar timestamps must include a UTC offset")
    return result.astimezone(UTC)


def read_bars(path):
    bars = []
    with Path(path).open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            bar = Bar(parse_timestamp(row["timestamp"]),
                      *(float(row[k]) for k in ("open", "high", "low", "close")))
            if not all(math.isfinite(p) and p > 0 for p in
                       (bar.open, bar.high, bar.low, bar.close)):
                raise ValueError("Nonpositive or invalid OHLC price")
            if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
                raise ValueError("Inconsistent OHLC prices")
            bars.append(bar)
    bars.sort(key=lambda b: b.timestamp)
    if not bars or len({b.timestamp for b in bars}) != len(bars):
        raise ValueError("Empty data or duplicate timestamps")
    return bars


def save_bars(path, bars):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp", "open", "high", "low", "close"])
        for b in bars:
            writer.writerow([b.timestamp.isoformat(), b.open, b.high, b.low, b.close])


def validate_coverage(bars, sessions, start, end):
    expected = set()
    for session in sessions:
        opening = parse_timestamp(session["start"])
        closing = parse_timestamp(session["end"])
        if not start <= opening.astimezone(NY).date() < end:
            continue
        while opening < closing:
            expected.add(opening)
            opening += timedelta(minutes=5)
    actual = {b.timestamp for b in bars if start <= b.timestamp.astimezone(NY).date() < end}
    if not expected:
        raise ValueError("No exchange sessions in the requested period")
    missing, extra = expected - actual, actual - expected
    if missing or extra:
        raise ValueError(f"Data coverage failed: {len(missing)} missing, {len(extra)} unexpected bars. "
                         "Do not interpret an incomplete download as a six-month test.")
    return len(expected)


def simulate(bars, start, end, commission=1.0, slippage_bps=1.0, capital=10000.0):
    """One share, long/flat, rolling SMA across sessions, no same-bar fills."""
    closes = []
    previous = None
    pending = None
    position = None
    cash = capital
    peak = capital
    drawdown = 0.0
    drawdown_pct = 0.0
    trades = []
    curve = []
    eligible = []
    slip = slippage_bps / 10000

    def close_position(bar, raw_price, reason):
        nonlocal cash, position
        price = raw_price * (1 - slip)
        cash += price - commission
        trades.append({"entry_time": position["time"], "exit_time": bar.timestamp.isoformat(),
                       "entry_price": position["price"], "exit_price": price,
                       "quantity": 1, "commission": commission * 2,
                       "net_pnl": price - position["price"] - commission * 2,
                       "exit_reason": reason})
        position = None

    for bar in bars:
        day = bar.timestamp.astimezone(NY).date()
        if day >= end:
            break
        active = start <= day < end
        if active:
            eligible.append(bar)
            if pending == "BUY" and position is None:
                price = bar.open * (1 + slip)
                if cash < price + commission:
                    raise ValueError("Insufficient starting capital for one share")
                cash -= price + commission
                position = {"time": bar.timestamp.isoformat(), "price": price}
            elif pending == "SELL" and position is not None:
                close_position(bar, bar.open, "crossover")
            pending = None
        closes.append(bar.close)
        if len(closes) >= 20:
            difference = mean(closes[-5:]) - mean(closes[-20:])
            if active and previous is not None:
                if previous <= 0 < difference and position is None:
                    pending = "BUY"
                elif previous >= 0 > difference and position is not None:
                    pending = "SELL"
            previous = difference
        if active:
            equity = cash + (bar.close if position else 0)
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
            drawdown_pct = max(drawdown_pct, (peak - equity) / peak * 100)
            curve.append({"timestamp": bar.timestamp.isoformat(), "equity": equity})
    warmup = sum(b.timestamp.astimezone(NY).date() < start for b in bars)
    if warmup < 20 or not eligible:
        raise ValueError("Need at least 20 pre-period warmup bars and bars in the test period")
    # Explicit reporting assumption: liquidate at final close, including costs.
    if position:
        close_position(eligible[-1], eligible[-1].close, "end_of_test_liquidation")
        curve[-1]["equity"] = cash
        drawdown = max(drawdown, peak - cash)
        drawdown_pct = max(drawdown_pct, (peak - cash) / peak * 100)
    gross_wins = sum(max(t["net_pnl"], 0) for t in trades)
    gross_losses = -sum(min(t["net_pnl"], 0) for t in trades)
    benchmark = (eligible[-1].close * (1 - slip)
                 - eligible[0].open * (1 + slip) - 2 * commission)
    summary = {
        "symbol": "SPY", "start_inclusive": str(start), "end_exclusive": str(end),
        "first_bar": eligible[0].timestamp.isoformat(), "last_bar": eligible[-1].timestamp.isoformat(),
        "bars": len(eligible), "initial_capital": capital, "final_equity": cash,
        "net_pnl": cash - capital, "return_pct": (cash / capital - 1) * 100,
        "closed_trades": len(trades),
        "win_rate_pct": (sum(t["net_pnl"] > 0 for t in trades) / len(trades) * 100) if trades else None,
        "profit_factor": gross_wins / gross_losses if gross_losses else None,
        "max_drawdown_dollars": drawdown,
        "max_drawdown_pct": drawdown_pct,
        "one_share_buy_hold_net_pnl": benchmark,
        "commission_per_order": commission, "slippage_bps_per_side": slippage_bps,
        "assumptions": ["5/20 SMA on completed 5-minute RTH candles; next-bar-open fills",
                        "One share long/flat, no shorting; averages carry across sessions",
                        "Positions may remain overnight; no stop loss",
                        "Final position liquidated at final close with costs",
                        "No dividends, taxes, interest or partial fills; no annualization",
                        "IBKR TRADES bars; corporate action adjustments follow IBKR data"],
    }
    return summary, trades, curve


def download(args):
    from ib_async import IB, Stock
    from bot import paper_account
    args.data.mkdir(parents=True, exist_ok=True)
    ib = IB()
    ib.RaiseRequestErrors = True
    ib.RequestTimeout = 120
    collected, sessions = {}, {}
    earliest = datetime.combine(args.start - timedelta(days=7), time(), NY)
    cursor = datetime.combine(args.end, time(), NY)
    try:
        ib.connect(args.host, args.port, clientId=args.client_id, readonly=True, timeout=15)
        paper_account(ib.managedAccounts())
        contracts = ib.qualifyContracts(Stock("SPY", "SMART", "USD"))
        if len(contracts) != 1:
            raise ValueError("SPY could not be uniquely qualified")
        while cursor > earliest:
            cache = args.data / ("week_" + cursor.strftime("%Y%m%d") + ".json")
            if cache.exists():
                chunk = json.loads(cache.read_text(encoding="utf-8"))
                print(f"Reusing {cache.name}", flush=True)
            else:
                print(f"Downloading week ending {cursor.isoformat()} ...", flush=True)
                bars = ib.reqHistoricalData(contracts[0], endDateTime=cursor,
                    durationStr="1 W", barSizeSetting="5 mins", whatToShow="TRADES",
                    useRTH=True, formatDate=2, timeout=120)
                schedule = ib.reqHistoricalSchedule(contracts[0], numDays=7,
                                                    endDateTime=cursor, useRTH=True)
                if not bars or not schedule.sessions:
                    raise ValueError("Empty weekly data/schedule. Check IBKR historical-data permissions.")
                zone = ZoneInfo(schedule.timeZone)

                def session_time(value):
                    return datetime.strptime(value, "%Y%m%d-%H:%M:%S").replace(
                        tzinfo=zone).astimezone(UTC).isoformat()

                chunk = {"bars": [{"timestamp": b.date.isoformat(), "open": b.open,
                                   "high": b.high, "low": b.low, "close": b.close} for b in bars],
                         "sessions": [{"start": session_time(s.startDateTime),
                                       "end": session_time(s.endDateTime)} for s in schedule.sessions]}
                cache.write_text(json.dumps(chunk, indent=2), encoding="utf-8")
                ib.sleep(2)
            for b in chunk["bars"]:
                collected[b["timestamp"]] = Bar(parse_timestamp(b["timestamp"]),
                    *(float(b[k]) for k in ("open", "high", "low", "close")))
            for session in chunk["sessions"]:
                sessions[session["start"]] = session
            cursor -= timedelta(days=7)
    finally:
        ib.disconnect()
    save_bars(args.data / "SPY_5min.csv", sorted(collected.values(), key=lambda b: b.timestamp))
    (args.data / "sessions.json").write_text(json.dumps(list(sessions.values()), indent=2), encoding="utf-8")
    print(f"Saved bars and exchange sessions in {args.data}")


def nonnegative(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Expected finite nonnegative number")
    return number


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["download", "run"])
    today = datetime.now(NY).date()
    p.add_argument("--start", type=date.fromisoformat, default=six_months_before(today))
    p.add_argument("--end", type=date.fromisoformat, default=today, help="Exclusive date")
    p.add_argument("--data", type=Path, default=ROOT / "data" / "spy_5min")
    p.add_argument("--output", type=Path, default=ROOT / "reports" / "sma_5_20")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497)
    p.add_argument("--client-id", type=int, default=18)
    p.add_argument("--commission", type=nonnegative, default=1.0)
    p.add_argument("--slippage-bps", type=nonnegative, default=1.0)
    p.add_argument("--capital", type=nonnegative, default=10000.0)
    args = p.parse_args()
    if args.start >= args.end or args.end > today:
        p.error("Use start < end <= today; end date is exclusive")
    try:
        if args.command == "download":
            download(args)
            return
        bars = read_bars(args.data / "SPY_5min.csv")
        sessions = json.loads((args.data / "sessions.json").read_text(encoding="utf-8"))
        validate_coverage(bars, sessions, args.start, args.end)
        summary, trades, curve = simulate(bars, args.start, args.end, args.commission,
                                         args.slippage_bps, args.capital)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        for name, rows in [("trades", trades), ("equity", curve)]:
            with (args.output / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
                if rows:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                elif name == "trades":
                    csv.writer(stream).writerow(["entry_time", "exit_time", "entry_price",
                        "exit_price", "quantity", "commission", "net_pnl", "exit_reason"])
        print(json.dumps(summary, indent=2))
        print(f"Reports saved in {args.output}")
    except Exception as exc:
        p.exit(1, f"Backtest failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
