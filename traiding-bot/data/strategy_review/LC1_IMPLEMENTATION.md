# Conditional LC-1 sequence implementation

Implemented in swing_lc1.py, check_swing_reference.py, with execution references
and the pure FX ledger from the previous stage. These checks do not constitute
automatic selection of structure, POIs or phases, or a full strategy backtest.

User timeframe correction: context fractal structure belongs to 4H/1H. On M15
the user treats the qualifying high/low near or inside the POI as INDUCEMENT,
even when it resembles a fractal pivot. The context mapper is not imported to
qualify LC-1. Exact inducement selection/strength remains annotated in these
examples; no numerical proximity cutoff or extra M15 context-CHoCH trend filter
has been introduced. Its liquidity role is confirmed; automatic selection is not.

Inducement qualification is now confirmed and implemented: a sell high must
cause a break of a previous M15 low, and a buy low must cause a break of a
previous M15 high. Wick crossing qualifies; closing confirmation adds quality.
qualify_inducement checks this from supplied M15 origin/prior candles. Their
selection remains a separate judgment. Proximity improves quality and is not
an eligibility filter. A prior
level from the future is rejected; an origin revisit before/with qualification
requires review. No 4H/1H context mapper is used to qualify the M15 liquidity.

Latest formation clarification supersedes the earlier left-leg-only reading:
any qualifying inducement near or inside the POI is eligible, including a point
formed during a pullback. A newer inducement to the right does not disqualify
LC-1. No no-PBID or left-leg-only admission filter is used. Left-leg higher lows
for buys/lower highs for sells remain valid examples, alongside other qualifying
formation locations. The opposite-level break and established LC entry rules
remain mandatory. Multiple qualifying points are permitted; origin/prior pairing
still uses selected inputs rather than automatic discovery.

Latest proximity clarification: any qualifying inducement may be used even
when farther from the POI. References are M15 entry-timeframe only. Signal
metadata reports distance in pips, with proximity_is_entry_filter=false; no
probability grade, distance cutoff or risk adjustment is inferred. Three new
checks cover far/inside levels and rejection of HTF inducement inputs, bringing
the relevant combined suite to 83 passing tests. January reference replays pass.

The latest user-drawn candle sketch is explicitly confirmed as a BUY example:
qualified left-leg higher low -> later low sweep into demand -> valid closed-LC
buy-stop at its high, stop at its low. Its position-box colors do not override
the user's direction. This explanatory sketch is not a new historical replay.

## What the code determines from candles

- Waits for a closed 1H break through an annotated level before activating an
  annotated originating candle's zone. Does not backdate availability.
- Detects the first qualifying opposite-level wick break for supplied M15
  origin/prior references; records close-versus-wick quality and availability.
- Watches minute ranges for POI touch, far-boundary invalidation and a sweep.
- Requires the liquidation M15 candle to close before emitting entry eligibility.
- Uses wick-only next-candle early invalidation before mitigation. Same-minute
  touch plus invalidation is conservatively rejected/flagged, not favorably ordered.
- Finds executable quote-side entry triggers after eligibility.
- Moves an unfilled entry and stop together after an overlapping M15 candle
  closes; each amendment requests a fresh risk plan.
- Stops amending after a fill. An invalid POI cancels pending eligibility.

## Deliberately unimplemented judgments

- Automatic choice/confirmation of fractal, internal and swing reference pivots.
- Automatic selection/ranking of originating POI candles and strong liquidity.
- Phase/context eligibility and probabilities: reference examples are approved
  annotations, not output from a learned or numerical classifier.
- LC-2A and LC-2B classification.
- Mitigation occurring after an earlier LC has closed: choosing the entry candle
  in that case is flagged for review, not silently assigned a new rule.
- Validity beyond the immediately next pre-touch candle, and replacement candles
  wholly outside the POI: flagged for review.

## January reference reconciliation

All times below are America/Halifax (UTC-4 in January).

| Case | Initial entry eligible | Amendment | Trigger minute | Price-path exit |
|---|---|---|---|---|
| Jan 23 | 10:30 after 10:15–10:30 LC | 10:45: entry 156.243 -> 156.322; stop 156.378 -> 156.405 | 10:51 | Stop |
| Jan 29 | 15:45 after 15:30–15:45 LC | None before fill | 15:51 | 2R target |

Signal times were not provided to the sequence scanner. They emerge conditionally
from the annotated POI origin, broken level, liquidity anchor and context approval.
Those input annotations still encode human selection and must not be described
as a blind or out-of-sample detector test.

The January 23 POI is a candidate 1H candle at 12:00 UTC, range 156.372–156.600;
the reference broken level is the 09:00 UTC 1H low 156.3505. Liquidity anchor:
13:15 UTC M15 high 156.3585; the qualification reference is the earlier 13:00 UTC
M15 low 156.252, closed below at 13:30, available at 13:45 UTC.

The January 29 origin/POI is the previously accepted mapping: 01:00 UTC 1H range
155.592–155.790; broken-level reference 155.050; initial close confirmation 06:00 UTC.
Liquidity anchor: 11:30 UTC M15 high 155.5225. This reconciliation now uses the
09:00 UTC M15 low 155.0905 as its annotated qualification reference (the earlier
H1 low happened to have the same value). The 15:15 UTC M15 candle wicks below
it, making the reference available at 15:30 UTC. The later close is not required.
These specific origin/prior choices remain annotations, not an automatic selector.

Each qualification reference candle closes before the associated liquidity
anchor begins. Actual structure-level selection is not inferred from the winners.

24 tests passed across the LC-1 state machine (10), risk ledger (9), and price-path
replay (5). The two real-data conditional reconciliations also pass. Full trace,
per-amendment risk plans and scope limitations: lc1_sequence_reconciliation.json.

Subsequent qualification stage: eight new tests pass, bringing the current combined
structure/LC-1 suite to 72 passing tests. The two selected January reconciliations
also pass with wick-based qualification; they are not a full strategy backtest.
