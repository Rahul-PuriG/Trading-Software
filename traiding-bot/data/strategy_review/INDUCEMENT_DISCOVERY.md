# Automatic M15 break-supported candidate discovery

Implemented in inducement_candidates.py, separately from the 1H/4H context
mapper. Eight new tests pass; the current relevant suite has 80 passing tests.
The detector emits candidates and review flags, never broker orders.

## Method and limits

Each completed M15 candle supplies a possible prior level. Subsequent highs
(SELL) or lows (BUY) can become candidate origins while that level remains
unbroken. When price breaks the prior opposite level, emit every origin that
has not already been crossed. Wick crossing qualifies; the source close adds
quality. Availability is at the completed break candle's end.

Retain multiple surviving origins and multiple supporting prior references.
There is no newest-only, global-extreme-only, left-leg-only or no-PBID rule.
An origin crossed with the qualifying break, or a possible break within the
origin candle itself, is marked review_required rather than accepted on an
assumed intrabar path. Quote gaps are flagged and not filled with invented bars.

This enumerates M15 entry-timeframe break-supported candidates. Proximity is
quality information only and never a maximum-distance admission filter. This
does not yet validate final HL/LH interpretation, identify POIs, assign phase/context,
select entries, or produce a full backtest. It does not reuse the HTF fractal
map to establish an M15 trend filter. Previously crossed candidate origins
are not silently certified as untouched origins for a later break.

## Actual-data comparison

Scanned all 6,043 supplied M15 candles, without supplying the two expected
inducement prices or origin times to detection. Comparison occurred afterward.

| Marked reference | Supporting prior-level pairs | Earliest completed-bar availability |
|---|---:|---|
| Jan 23 13:15 UTC high 156.3585 | 4 | Jan 23 13:45 UTC |
| Jan 29 11:30 UTC high 155.5225 | 9 | Jan 29 12:15 UTC |

The Jan 29 earliest candidate is supported by a smaller, earlier-broken M15
level than the manually selected 09:00 low used in the reference reconciliation.
That particular prior-level pairing still qualifies at 15:30 UTC. Do not
confuse discovering the same origin with validating its final reference pairing.

The scan yields 37,905 qualified origin/prior pairs representing 4,165 distinct
side/origin/price points, plus 13,456 review-required pair cases. These are raw
candidate counts, not trade counts. No proximity or quality threshold was fitted
to the recorded outcomes. Thirty-three generated pair checks (20 initial sample
pairs and all 13 supports for the marked references) also pass the independent
selected-reference qualify_inducement checker for price, timing and quality.

## Artifacts and next dependency

inducement_candidate_pairs.csv contains all pairs. inducement_candidate_audit.json
contains counts, samples, post-scan reference comparisons and independent checks.

The user resolved near/inside POI as quality-only: distance does not disqualify
a valid candidate. Candidate events declare source_timeframe_minutes=15 and
proximity_is_entry_filter=false. LC-1 signal metadata reports distance to the
POI in pips without inventing a threshold or automatic probability grade.
No same-candle mitigation requirement has been invented.
Candidate lifecycle, POI/context selection and LC entry sequencing must be
connected and validated before these candidates can become automatic trades.

Three additional LC-1 policy checks bring the current relevant suite to 83 tests.
