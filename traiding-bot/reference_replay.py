"""Price-path checks for two manually selected journal candidates, not signal detection.

No orders, position sizing, commissions, financing or strategy profitability.
OHLC event times refer to minute bars, not exact execution seconds.
"""

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from backtest import ROOT, read_bars

LOCAL = ZoneInfo("America/Halifax")


REFERENCES = [
    {"id": "round3_row3_2025_01_23", "side": "SELL",
     "signal_bar_start": "2025-01-23T14:30:00+00:00"},
    {"id": "round3_row4_2025_01_29", "side": "SELL",
     "signal_bar_start": "2025-01-29T19:30:00+00:00"},
]


def replay(signal, minutes, side="SELL", spread_pips=1.0, slippage_pips=0.1, reward_r=2.0):
    if side not in {"BUY", "SELL"} or spread_pips < 0 or slippage_pips < 0 or reward_r <= 0:
        raise ValueError("Invalid side, spread, slippage or target")
    direction = 1 if side == "BUY" else -1
    half = spread_pips * 0.01 / 2
    slip = slippage_pips * 0.01
    entry_level = signal.high if side == "BUY" else signal.low
    stop_level = signal.low if side == "BUY" else signal.high
    available = signal.timestamp + timedelta(minutes=15)
    expires = available + timedelta(minutes=15)
    result = {"side": side, "signal_bar_start_utc": signal.timestamp.isoformat(),
              "entry_active_from_utc": available.isoformat(), "entry_level": entry_level,
              "stop_level": stop_level, "spread_pips": spread_pips,
              "slippage_pips": slippage_pips, "reward_r": reward_r,
              "scope": "One initial pending-entry window only; no LC/phase/POI detection or amendments",
              "status": "not_triggered_in_initial_window"}
    entry = target = None
    for bar in minutes:
        if bar.timestamp < available:
            continue
        new_entry = False
        if entry is None:
            if bar.timestamp >= expires:
                break
            executable_open = bar.open + direction * half
            crossed = (bar.high + half >= entry_level) if side == "BUY" else (bar.low - half <= entry_level)
            if not crossed:
                continue
            entry = ((max(entry_level, executable_open) + slip) if side == "BUY"
                     else (min(entry_level, executable_open) - slip))
            distance = direction * (entry - stop_level)
            if distance <= 0:
                raise ValueError("Entry at/beyond protective stop")
            target = entry + direction * reward_r * distance
            new_entry = True
            result.update(status="open_at_data_end", entry_price=entry, target_level=target,
                          entry_minute_utc=bar.timestamp.isoformat(),
                          entry_minute_halifax=bar.timestamp.astimezone(LOCAL).isoformat())
        # Exits use the opposite quote side. A long sells at bid; a short buys at ask.
        exit_open = bar.open - direction * half
        exit_high = bar.high - direction * half
        exit_low = bar.low - direction * half
        stop_hit = exit_low <= stop_level if side == "BUY" else exit_high >= stop_level
        target_hit = exit_high >= target if side == "BUY" else exit_low <= target
        if not stop_hit and not target_hit:
            continue
        # Existing orders at the opening price precede subsequent candle extremes.
        gap_stop = not new_entry and (exit_open <= stop_level if side == "BUY" else exit_open >= stop_level)
        gap_target = not new_entry and (exit_open >= target if side == "BUY" else exit_open <= target)
        if gap_stop:
            reason, price = "gap_stop", exit_open - direction * slip
        elif gap_target:
            reason, price = "target", target  # Conservative: no favorable limit improvement.
        elif stop_hit:
            reason, price = "stop", stop_level - direction * slip
        else:
            reason, price = "target", target
        result.update(status="closed", exit_reason=reason, exit_price=price,
                      exit_minute_utc=bar.timestamp.isoformat(),
                      exit_minute_halifax=bar.timestamp.astimezone(LOCAL).isoformat(),
                      price_r_before_commission=direction*(price-entry)/abs(entry-stop_level),
                      ambiguous_stop_target_bar=bool(stop_hit and target_hit and not gap_stop and not gap_target),
                      entry_exit_same_minute=new_entry)
        return result
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--context", type=Path, default=ROOT/"data/usdjpy_sample/USDJPY_context_15min.csv")
    p.add_argument("--minutes", type=Path, default=ROOT/"data/usdjpy_sample/USDJPY_execution_1min.csv")
    p.add_argument("--output", type=Path, default=ROOT/"data/strategy_review/reference_replay.json")
    args = p.parse_args()
    context = {b.timestamp: b for b in read_bars(args.context)}
    minutes = read_bars(args.minutes)
    # Use context coverage to distinguish missing execution data from periods
    # where neither timeframe has quotes (e.g. the observed daily FX break).
    expected_minutes = {bar.timestamp + timedelta(minutes=i)
                        for bar in context.values() for i in range(15)}
    output = []
    for reference in REFERENCES:
        signal = context[datetime.fromisoformat(reference["signal_bar_start"])]
        for label, spread, slip in [("zero_cost_diagnostic", 0, 0), ("assumed_spread_slippage", 1, .1)]:
            result = replay(signal, minutes, reference["side"], spread, slip)
            if "entry_minute_utc" in result:
                start = datetime.fromisoformat(result["entry_minute_utc"])
                end = datetime.fromisoformat(result.get("exit_minute_utc", minutes[-1].timestamp.isoformat()))
                stamps = {b.timestamp for b in minutes if start <= b.timestamp <= end}
                missing = {t for t in expected_minutes if start <= t <= end} - stamps
                if missing:
                    raise ValueError(f"Missing minute {min(missing).isoformat()} in reference path")
            output.append({"reference": reference["id"], "scenario": label, **result})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"not_a_strategy_backtest": True,
        "limitations": ["Manually selected candidate signal bars; eligibility not automatically detected",
            "Synthetic constant spread, approximate one-minute event ordering",
            "Quote gaps shared by both timeframes are retained; stops checked at next available quote",
            "No margin sizing, commission, financing or performance claim"],
        "reference_cases": output}, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
