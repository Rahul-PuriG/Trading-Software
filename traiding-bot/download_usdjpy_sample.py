"""Read-only IBKR USDJPY candle download for journal reconciliation, not trading."""

import argparse
import csv
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from ib_async import IB, Forex
from bot import paper_account

LOCAL = ZoneInfo("America/Halifax")
UTC = timezone.utc
ROOT = Path(__file__).resolve().parent


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def serialize_bar(bar):
    if not isinstance(bar.date, datetime) or bar.date.tzinfo is None:
        raise ValueError("Expected timezone-aware intraday timestamps from IBKR formatDate=2")
    values = {name: float(getattr(bar, name)) for name in ("open", "high", "low", "close")}
    if not all(math.isfinite(v) and v > 0 for v in values.values()):
        raise ValueError("Invalid OHLC price from historical-data service")
    if not values["low"] <= min(values["open"], values["close"]) <= max(values["open"], values["close"]) <= values["high"]:
        raise ValueError("Inconsistent OHLC prices")
    return {"timestamp": bar.date.astimezone(UTC).isoformat(), **values}


def expected_minute_slots(context_rows, start, end):
    begin = datetime.combine(start, time(), LOCAL).astimezone(UTC)
    finish = datetime.combine(end, time(), LOCAL).astimezone(UTC)
    return {stamp + timedelta(minutes=i)
            for row in context_rows
            for stamp in [datetime.fromisoformat(row["timestamp"])]
            for i in range(15) if begin <= stamp + timedelta(minutes=i) < finish}


def coverage_report(context_rows, execution_rows, start, end):
    expected = expected_minute_slots(context_rows, start, end)
    actual = {datetime.fromisoformat(row["timestamp"]) for row in execution_rows}
    missing, extra = sorted(expected - actual), sorted(actual - expected)
    return {"status": "passed" if expected and not missing and not extra else "failed",
            "basis": "Minute slots within downloaded 15-minute MIDPOINT bars; not an independent exchange calendar",
            "expected_minutes": len(expected), "actual_minutes": len(actual),
            "missing_minutes": len(missing), "unexpected_minutes": len(extra),
            "first_missing_minutes": [stamp.isoformat() for stamp in missing[:20]],
            "first_unexpected_minutes": [stamp.isoformat() for stamp in extra[:20]]}


def collect_series(ib, contract, start, end, minutes, folder, expected_times=None):
    if not start < end or minutes not in (1, 15):
        raise ValueError("Use start < end and a 1- or 15-minute bar size")
    begin = datetime.combine(start, time(), LOCAL).astimezone(UTC)
    finish = datetime.combine(end, time(), LOCAL).astimezone(UTC)
    cursor = finish
    cache = folder / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    combined = {}
    empty_requests = []
    # Daily requests at midnight produced partial FX trading sessions in the real
    # uploaded sample. Use explicit four-hour windows for one-minute bars instead.
    step = timedelta(hours=4) if minutes == 1 else timedelta(days=7)
    while cursor > begin:
        if minutes == 1 and expected_times is not None and not any(
                max(begin, cursor - step) <= stamp < cursor for stamp in expected_times):
            cursor -= step
            continue
        request = {"contract_id": contract.conId, "pair": "USDJPY", "exchange": "IDEALPRO",
                   "end_utc": cursor.isoformat(), "minutes": minutes, "what_to_show": "MIDPOINT",
                   "duration": "14400 S" if minutes == 1 else "1 W", "use_rth": False}
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()[:24]
        cached = cache / f"{minutes}min_{key}.json"
        if cached.exists():
            chunk = json.loads(cached.read_text(encoding="utf-8"))
            if chunk["request"] != request:
                raise ValueError("Cache metadata mismatch")
            rows = chunk["bars"]
            print(f"Reusing {minutes}-minute chunk ending {cursor.isoformat()}", flush=True)
        else:
            print(f"Downloading {minutes}-minute chunk ending {cursor.isoformat()}", flush=True)
            response = ib.reqHistoricalData(contract, endDateTime=cursor,
                durationStr=request["duration"], barSizeSetting="1 min" if minutes == 1 else "15 mins",
                whatToShow="MIDPOINT", useRTH=False, formatDate=2, timeout=120)
            rows = [serialize_bar(b) for b in response]
            # Empty windows can be weekends/holidays. Preserve that fact,
            # and do not turn it into a claim of complete market coverage.
            if rows:
                atomic_json(cached, {"request": request, "bars": rows})
            ib.sleep(2)
        if not rows:
            empty_requests.append(request["end_utc"])
        for row in rows:
            stamp = datetime.fromisoformat(row["timestamp"])
            if begin <= stamp < finish:
                if stamp in combined and combined[stamp] != row:
                    raise ValueError("Overlapping requests returned conflicting OHLC values")
                combined[stamp] = row
        cursor -= step
    rows = [combined[stamp] for stamp in sorted(combined)]
    if not rows:
        raise ValueError("No bars downloaded. Check TWS historical-data permissions and dates.")
    counts = {}
    for row in rows:
        day = datetime.fromisoformat(row["timestamp"]).astimezone(LOCAL).date().isoformat()
        counts[day] = counts.get(day, 0) + 1
    return rows, {"start_local_inclusive": str(start), "end_local_exclusive": str(end),
                  "minutes": minutes, "bars": len(rows), "first_bar": rows[0]["timestamp"],
                  "last_bar": rows[-1]["timestamp"], "bars_per_local_date": counts,
                  "empty_request_endpoints": empty_requests}


def write_csv(path, rows):
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["timestamp", "open", "high", "low", "close"])
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497)
    p.add_argument("--client-id", type=int, default=19)
    p.add_argument("--context-start", type=date.fromisoformat, default=date(2024, 11, 1))
    p.add_argument("--context-end", type=date.fromisoformat, default=date(2025, 2, 1))
    p.add_argument("--entry-start", type=date.fromisoformat, default=date(2025, 1, 22))
    p.add_argument("--entry-end", type=date.fromisoformat, default=date(2025, 1, 31))
    p.add_argument("--output", type=Path, default=ROOT / "data" / "usdjpy_sample")
    args = p.parse_args()
    today = datetime.now(LOCAL).date()
    if not args.context_start <= args.entry_start < args.entry_end <= args.context_end <= today:
        p.error("Require context-start <= entry-start < entry-end <= context-end <= today")
    ib = IB()
    ib.RequestTimeout = 120
    ib.RaiseRequestErrors = True
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        ib.connect(args.host, args.port, clientId=args.client_id, timeout=15, readonly=True)
        paper_account(ib.managedAccounts())
        contracts = ib.qualifyContracts(Forex("USDJPY"))
        if len(contracts) != 1:
            raise ValueError("USDJPY contract could not be uniquely qualified")
        contract = contracts[0]
        metadata = {"source": "IBKR IDEALPRO historical MIDPOINT", "contract_id": contract.conId,
                    "downloader_version": 2,
                    "timestamps": "UTC, timezone-aware bar-start timestamps",
                    "request_date_boundaries": "America/Halifax local midnight, end exclusive",
                    "purpose": "Journal reconciliation sample; not strategy performance",
                    "limitations": ["OANDA/FXReplay chart matching has not been established",
                        "MIDPOINT is not executable bid/ask; costs are not embedded",
                        "Coverage must be audited, including empty requests and FX maintenance gaps",
                        "No 4H/daily aggregation anchor or structure labels have been inferred",
                        "No orders submitted; no backtest results generated"], "series": {}}
        context_rows = None
        for label, start, end, minutes in [
            ("context_15min", args.context_start, args.context_end, 15),
            ("execution_1min", args.entry_start, args.entry_end, 1),
        ]:
            expected = expected_minute_slots(context_rows, start, end) if minutes == 1 else None
            rows, details = collect_series(ib, contract, start, end, minutes, args.output, expected)
            if minutes == 15:
                context_rows = rows
            filename = f"USDJPY_{label}.csv"
            if minutes == 1:
                metadata["execution_coverage"] = coverage_report(context_rows, rows, start, end)
                if metadata["execution_coverage"]["status"] != "passed":
                    filename = "USDJPY_execution_1min_INCOMPLETE.csv"
                    write_csv(args.output / filename, rows)
                    metadata["series"][label] = {"file": filename, **details}
                    atomic_json(args.output / "metadata.json", metadata)
                    raise ValueError("Minute coverage failed; see metadata.json and INCOMPLETE.csv. "
                                     "Do not use the prior execution CSV as a validated replacement.")
            write_csv(args.output / filename, rows)
            metadata["series"][label] = {"file": filename, **details}
            atomic_json(args.output / "metadata.json", metadata)
        print(f"Sample saved in {args.output}")
        print("Share USDJPY_context_15min.csv, USDJPY_execution_1min.csv and metadata.json.")
        print("Minute coverage matches downloaded 15-minute bars. Journal matching and strategy rules still require validation.")
        return 0
    except Exception as exc:
        print(f"Download failed: {type(exc).__name__}: {exc}")
        print("No orders were sent. Successfully cached nonempty chunks can be reused on retry.")
        return 1
    finally:
        ib.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
