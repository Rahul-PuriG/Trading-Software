# Automatic inducement connection to LC-1

Implemented in swing_lc1.scan_lc1_candidates. check_lc1_discovery.py supplies
annotated H1 zone origins/confirming levels and approved context, but does not
supply marked M15 liquidity origins/prices or expected signal times. Those
reference signals are compared only after detection.

## Behavior and scope

- Consume only qualified M15 candidate events of the zone's trade direction.
- Keep multiple distinct points. Merge duplicate supports for the same origin
  and price using earliest available break evidence.
- Do not apply a proximity, age, formation-type, left-leg-only or PBID threshold.
- Exclude a point visibly taken before the setup's execution window so it is
  not silently reused as fresh liquidity. This freshness handling is an explicit
  implementation interpretation; it does not settle all future re-entry cases.
- Feed retained points through the existing mitigation/sweep/closed-LC logic.
- Merge identical signal candles with multiple supporting inducement points;
  do not create one order per supporting prior-level pair.
- After an old zone touch, a later liquidation candle wholly outside the zone
  requires review. It is not an automatic entry merely because mitigation
  happened at some earlier time. Previously permitted pre-touch/late-mitigation
  cases retain their review flags; no new entry candle rule is invented.

This is not a live state machine or full strategy backtest. The zone and context
remain supplied. Signals are independently traced through pending-entry logic;
their portfolio interactions, changing phase and fresh re-entry validity are
not inferred. Missing pre-window coverage cannot prove a reference is fresh.
Same-minute conflicts and other unresolved cases remain review-required.

## Corrected actual-data result

| Supplied POI | First signal UTC | First fill UTC | Amendment count |
|---|---|---|---:|
| Jan 23 | Jan 23 14:30 | Jan 23 14:51 | 1 |
| Jan 29 | Jan 29 19:45 | Jan 29 19:51 | 0 |

Both expected initial signals emerge from the full discovered candidate bank.
The corresponding marked M15 price/origin and expected time are not detector
inputs. Automatic HTF POI discovery and phase approval are still unimplemented.

The Jan 23 zone yields six distinct candidate signal candles over the remaining
sample, including candidates on Jan 24; Jan 29 yields one. The context input is
constant/approved for the whole supplied zone trace, so additional Jan 23 signals
cannot be declared valid trades without dynamic context/re-entry validation.
An exploratory run before the old-touch correction produced far more signals;
that output was replaced by the corrected run, not treated as a valid result.

Seven new tests cover duplicate supports, merged signals, consumed references,
future/review events, timeframe/context enforcement and stale POI-touch handling.
The targeted structure/LC suite has 90 passing tests. The full Python suite passes all 136 tests.

Artifact: lc1_automatic_inducement_connection.json. Reproduce using:

    python check_lc1_discovery.py --context data/strategy_review/usdjpy_sample_audit/USDJPY_context_15min.csv --minutes data/strategy_review/usdjpy_sample_audit/USDJPY_execution_1min_v2.csv --candidates data/strategy_review/inducement_candidate_pairs.csv --reference-report data/strategy_review/lc1_sequence_reconciliation.json
