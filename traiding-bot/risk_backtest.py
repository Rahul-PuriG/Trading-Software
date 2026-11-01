"""Long-only SMA10/30 + SMA100, signal-low stop, equity-risk sizing and R target."""

import argparse
import csv
from datetime import date, datetime, timedelta
import json
import math
from pathlib import Path
from statistics import mean

from backtest import (NY, ROOT, aggregate_30min, nonnegative, read_bars,
                      six_months_before, validate_coverage)


def build_signals(bars, start, end, buffer):
    candles = aggregate_30min(bars)
    if sum(b.timestamp.astimezone(NY).date() < start for b in candles) < 100:
        raise ValueError("Need 100 pre-period 30-minute candles for warmup")
    closes, previous, signals = [], None, {}
    for candle in candles:
        closes.append(candle.close)
        if len(closes) < 30:
            continue
        difference = mean(closes[-10:]) - mean(closes[-30:])
        if len(closes) >= 100 and start <= candle.timestamp.astimezone(NY).date() < end:
            if previous is not None and previous <= 0 < difference and candle.close > mean(closes[-100:]):
                signals[candle.timestamp + timedelta(minutes=30)] = ("BUY", candle.low - buffer)
            elif previous is not None and previous >= 0 > difference:
                signals[candle.timestamp + timedelta(minutes=30)] = ("SELL", None)
        previous = difference
    return signals


def simulate_risk(bars, signals, start, end, capital=10000.0, risk_pct=1.0,
                  reward_r=3.3, commission=1.0, slippage_bps=1.0):
    if not capital > 0 or not 0 < risk_pct <= 100 or reward_r <= 0 or not 0 <= slippage_bps < 10000:
        raise ValueError("Use positive capital/R target, risk in (0,100] and slippage below 10000 bps")
    slip = slippage_bps / 10000
    cash = peak = capital
    position = pending = None
    trades, curve, eligible = [], [], []
    max_dd = max_dd_pct = 0.0
    skipped = cash_capped = ambiguous = 0

    def exit_trade(bar, raw_price, reason, is_limit=False):
        nonlocal cash, position
        # A target is a sell limit: never model a fill below its limit.
        price = raw_price if is_limit else raw_price * (1 - slip)
        q = position["quantity"]
        cash += q * price - commission
        pnl = q * (price - position["entry_price"]) - 2 * commission
        trades.append({**position, "exit_time": bar.timestamp.isoformat(),
                       "exit_price": price, "exit_reason": reason,
                       "commission": 2 * commission, "net_pnl": pnl,
                       "net_r": pnl / position["planned_stop_risk"]})
        position = None

    for bar in bars:
        if not start <= bar.timestamp.astimezone(NY).date() < end:
            continue
        eligible.append(bar)
        # Existing protective orders take precedence over discretionary exits.
        if position:
            if bar.open <= position["stop_price"]:
                exit_trade(bar, bar.open, "gap_stop")
            elif bar.open >= position["target_price"]:
                exit_trade(bar, position["target_price"], "target", is_limit=True)
        if pending:
            action, stop = pending
            if action == "SELL" and position:
                exit_trade(bar, bar.open, "crossover")
            elif action == "BUY" and position is None:
                entry = bar.open * (1 + slip)
                budget = cash * risk_pct / 100
                per_share_risk = entry - stop * (1 - slip)
                if stop <= 0 or bar.open <= stop or per_share_risk <= 0:
                    skipped += 1
                else:
                    risk_qty = max(0, math.floor((budget - 2 * commission) / per_share_risk))
                    cash_qty = max(0, math.floor((cash - commission) / entry))
                    quantity = min(risk_qty, cash_qty)
                    if quantity < 1:
                        skipped += 1
                    else:
                        cash_capped += int(cash_qty < risk_qty)
                        planned_risk = quantity * per_share_risk + 2 * commission
                        position = {"entry_time": bar.timestamp.isoformat(), "entry_price": entry,
                                    "quantity": quantity, "stop_price": stop,
                                    "target_price": entry + reward_r * (entry - stop),
                                    "risk_budget": budget, "planned_stop_risk": planned_risk}
                        cash -= quantity * entry + commission
            pending = None
        # Protective orders are active during the entry bar too.
        if position:
            stop_hit = bar.low <= position["stop_price"]
            target_hit = bar.high >= position["target_price"]
            ambiguous += int(stop_hit and target_hit)
            if stop_hit:
                exit_trade(bar, position["stop_price"], "stop")
            elif target_hit:
                exit_trade(bar, position["target_price"], "target", is_limit=True)
        equity = cash + (position["quantity"] * bar.close if position else 0)
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        max_dd_pct = max(max_dd_pct, (peak - equity) / peak * 100)
        curve.append({"timestamp": bar.timestamp.isoformat(), "equity": equity})
        signal = signals.get(bar.timestamp + timedelta(minutes=5))
        if signal and ((signal[0] == "BUY" and position is None)
                       or (signal[0] == "SELL" and position is not None)):
            pending = signal
    if not eligible:
        raise ValueError("No bars in test period")
    if position:
        exit_trade(eligible[-1], eligible[-1].close, "end_of_test_liquidation")
        curve[-1]["equity"] = cash
        max_dd = max(max_dd, peak - cash)
        max_dd_pct = max(max_dd_pct, (peak - cash) / peak * 100)
    wins = [t["net_pnl"] for t in trades if t["net_pnl"] > 0]
    losses = [t["net_pnl"] for t in trades if t["net_pnl"] < 0]
    benchmark_qty = max(0, math.floor((capital - commission) / (eligible[0].open * (1 + slip))))
    benchmark_pnl = (benchmark_qty * (eligible[-1].close * (1 - slip)
                     - eligible[0].open * (1 + slip)) - 2 * commission) if benchmark_qty else 0
    summary = {"symbol": "SPY", "strategy": "30min SMA10/30, close above SMA100, long only",
               "start_inclusive": str(start), "end_exclusive": str(end),
               "initial_capital": capital, "final_equity": cash,
               "net_pnl": cash - capital, "return_pct": (cash/capital - 1)*100,
               "closed_trades": len(trades),
               "win_rate_pct": len(wins)/len(trades)*100 if trades else None,
               "profit_factor": sum(wins)/-sum(losses) if losses else None,
               "max_drawdown_dollars": max_dd, "max_drawdown_pct": max_dd_pct,
               "risk_pct": risk_pct, "target_r_multiple": reward_r,
               "commission_per_order": commission, "slippage_bps_per_side": slippage_bps,
               "total_commissions": 2*commission*len(trades),
               "cash_capped_entries": cash_capped, "skipped_entries": skipped,
               "ambiguous_5min_bars_stop_first": ambiguous,
               "cash_matched_buy_hold_quantity": benchmark_qty,
               "cash_matched_buy_hold_net_pnl": benchmark_pnl,
               "exit_counts": {reason: sum(t["exit_reason"] == reason for t in trades)
                               for reason in sorted({t["exit_reason"] for t in trades})},
               "assumptions": ["Completed 30-minute signals, next available 5-minute open entry",
                   "Stop below signal candle low minus buffer; target 3.3R by default before costs",
                   "Exit at stop, target or bearish crossover, whichever is first; no short entries",
                   "Risk sizing includes estimated stop slippage and round-trip commissions",
                   "Whole shares, cash capped, no leverage; actual planned risk can be below budget",
                   "Stops/targets checked on 5-minute OHLC; both touched means stop first",
                   "Stop gaps fill at opening price less slippage; losses may exceed 1%",
                   "Targets fill at limit, including gaps above; fills/available liquidity not guaranteed",
                   "Equity marked every 5 minutes; intrabar drawdown is not measured",
                   "Hold overnight; final liquidation at last close with costs",
                   "No dividends, interest, taxes or partial fills"]}
    return summary, trades, curve


def main():
    p = argparse.ArgumentParser(description=__doc__)
    today = datetime.now(NY).date()
    p.add_argument("--start", type=date.fromisoformat, default=six_months_before(today))
    p.add_argument("--end", type=date.fromisoformat, default=today)
    p.add_argument("--data", type=Path, default=ROOT / "data" / "spy_5min")
    p.add_argument("--output", type=Path, default=ROOT / "reports" / "risk1_rr3_3")
    p.add_argument("--capital", type=nonnegative, default=10000)
    p.add_argument("--risk-pct", type=nonnegative, default=1)
    p.add_argument("--reward-r", type=nonnegative, default=3.3)
    p.add_argument("--buffer", type=nonnegative, default=0.05, help="Dollars below signal candle low")
    p.add_argument("--commission", type=nonnegative, default=1)
    p.add_argument("--slippage-bps", type=nonnegative, default=1)
    args = p.parse_args()
    if not args.start < args.end <= today:
        p.error("Use start < end <= today (end exclusive)")
    try:
        bars = read_bars(args.data / "SPY_5min.csv")
        sessions = json.loads((args.data / "sessions.json").read_text(encoding="utf-8"))
        validate_coverage(bars, sessions, args.start, args.end)
        signals = build_signals(bars, args.start, args.end, args.buffer)
        summary, trades, curve = simulate_risk(bars, signals, args.start, args.end,
            args.capital, args.risk_pct, args.reward_r, args.commission, args.slippage_bps)
        summary["buffer_dollars"] = args.buffer
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        for name, records in [("trades", trades), ("equity", curve)]:
            with (args.output / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
                keys = list(records[0]) if records else ["entry_time", "exit_time", "net_pnl"]
                writer = csv.DictWriter(stream, fieldnames=keys)
                writer.writeheader()
                writer.writerows(records)
        print(json.dumps(summary, indent=2))
        print(f"Reports saved in {args.output}")
    except Exception as exc:
        p.exit(1, f"Risk backtest failed: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
