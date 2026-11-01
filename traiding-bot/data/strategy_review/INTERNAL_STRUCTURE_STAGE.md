# Internal pullback confirmation stage

The user confirmed that a pullback extreme remains a candidate until an internal
BOS closes beyond the prior internal high or low. This is implemented in
internal_structure.py with bullish and bearish cases.

Timeframe correction: this context hierarchy is mapped on 4H/1H. The context
wrapper rejects M15; the user's distinct M15 LC-1 fractal CHoCH is not supplied
by this tracker. Earlier M15 demonstrations do not validate that LC-1 rule.

## State sequence

1. Start with explicitly supplied internal direction and high/low boundaries.
2. An opposing fractal-direction change starts the internal pullback.
3. Track its extreme as a candidate. Restored fractal alignment suggests the
   pullback is ending; it does not confirm the internal pivot.
4. A candle close beyond the prior continuation level confirms the pivot, with
   availability at that candle's close. A wick or equal close is insufficient.
5. A close through the protected opposite boundary reverses internal direction.
   A fractal reversal or wick through that boundary alone does not reverse it.

The user also confirmed the illustrated active-level example: after a newer
fractal low at 150.30 is confirmed, its break to 150.20 starts the internal
pullback even while the older 150.00 fractal low holds. No new internal BOS is
required before acting on the newer confirmed fractal point. Mirror for a newer
confirmed high in bearish internal structure. Tests exercise the wick break of
the supplied newer reference, followed by the internal pullback transition.

The 36–50% retracement band is reported as a preference, never an eligibility
filter. The diagnostic calculation uses the supplied prior leg boundaries;
the user has not yet confirmed those exact Fibonacci endpoints.

## Limits

This is conditional state tracking. Initial boundaries and timestamped controlling
fractal-direction evidence are supplied separately. It does not select the active
A from nested fractal candidates, initialize the full hierarchy, assign swing
phases, select POIs, or send orders. It is not an automated strategy backtest.

Updates consume completed source candles. An event's known_at is distinct from
the older pivot-origin timestamp. Callers must wait for that availability before
using an event on a lower timeframe. Missing candle intervals are not filled;
input coverage and the completeness of direction evidence remain caller duties.

Run python -m unittest test_internal_structure -v. Checks cover both directions,
candidate-versus-confirmed timing, wick/equal-close rejection, internal reversal,
soft depth preference, future evidence, bad OHLC and overlapping candles.
Additional integration checks cover the newer confirmed reference breaking
while the older reference and protected internal boundary hold, in both directions.
