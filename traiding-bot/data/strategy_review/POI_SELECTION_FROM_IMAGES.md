# POI origin selection from the user's two annotated sketches

The user supplied these sketches specifically to explain how to select POIs.
Apply them with the latest confirmed rules in CURRENT_SPEC.md. This document
records the selection logic; it is not an implementation/test result.

## What the pictures establish

Look in the LEFT leg responsible for the confirmed structure break. In the
bullish drawings, the origin extreme at the low of that leg is one demand POI
source. A subsequent mid-leg origin with an inducement sweep, marked x, is
another highlighted source. The resulting move produces the labelled i-BOS.
Mirror the relationship for bearish supply origins at highs.

These are possible qualifying origin areas, not a rule to shade every candle
before BOS. Once the actual origin candle is identified, use its ONE full
high-low range including wicks, irrespective of candle color, as already agreed.
The leg may contain more than two separately valid POIs.

Extreme origin and mid-leg sweep origin are both allowed. Prefer the more
extreme location for contextual quality when the other requirements hold;
do not reject valid mid-leg zones merely because a deeper zone exists.
An inducement sweep at the source strengthens the POI. The pictures do not
establish a universal exclusion of all mid-leg zones without that confluence.

## Timing and separation of roles

The zone must lead to a qualifying confirmed structure break and initially be
unmitigated. Confirmed internal/swing breaks still require a close. An origin
timestamp identifies the candle; it must not backdate availability to a point
before the required structure confirmation.

The sweep drawn as an HTF POI confluence is distinct from the M15 inducement
used for LC-1 entry. Entry inducement is searched only on the entry timeframe.
POI proximity remains quality-only for entry inducement; no distance threshold
or automatic HIGH-probability classification is added by these pictures.

After creation, retain the existing mitigation, immediate far-edge invalidation,
fresh setup/re-entry and LC entry rules. A good-looking source is not itself
an entry signal.

## Implementation still required

Connect causal 4H/1H structure/leg discovery to the candidate origin extreme
and mid-leg sweep sources, then compare selected full candle ranges with the
existing annotated journal zones. Leg initialization and ambiguous source
pairings remain implementation/validation tasks. No new POI detector or test
count is claimed from this documentation update.

The inline sketches are described here because their original binaries are not
available as local attachment files. The first callout's final sentence was
truncated; no additional requirement is inferred from the missing text.
