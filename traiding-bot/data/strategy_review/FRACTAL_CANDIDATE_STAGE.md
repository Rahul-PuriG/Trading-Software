# Confirmed multi-candle pullback pattern — candidate stage

Implemented in fractal_candidates.py. Ten new tests pass.

Scope correction: the user's context fractal structure is on 4H/1H. Historical
M15 scans below are generic pattern diagnostics, not the user's M15 LC-1 rule
and not validation of the context structure map. The subsequent context mapper
rejects M15. Keep original diagnostic counts as historical evidence only.

## Sequential reset rule — subsequently confirmed

FractalSequenceDetector now follows one active A in a supplied direction:

1. Use the first supplied candle as A.
2. Before any failure, move A to each new higher-high candle (bullish) or
   lower-low candle (bearish). No failure means no pullback to confirm.
3. The first failure freezes A. Keep that original level through all subsequent
   failures and retain their opposite extreme, including ties and source times.
4. C breaking that frozen level confirms the intervening extreme, subject to
   the existing outside-candle ordering review. C starts the next sequence.

The user's confirmed diagram yields two bullish fractal lows: B at 150.20 on
C's break of A, then E at 150.70 on F's break of D. D replaces C as A because D
makes a higher high before E fails. The bearish rule mirrors this sequence.

Ten additional sequence tests pass; combined with the original candidate,
internal-state and break-evidence checks, 36 tests pass. Ambiguous outside
breakouts emit a review-required candidate with confirmed=false. Completed-bar
availability remains at C's close; reference origin is not confirmation time.

Direction and first candle are explicit inputs. Automatic direction changes,
resetting on fractal CHoCH and internal/swing initialization remain unfinished.
The historical nested enumeration described below is retained as a diagnostic.

The new detector was also scanned over the 6,043 M15 and 1,465 H1 bars, separately
in each supplied direction, from the first November candle. These fixed-direction
scans do not reproduce the four January reference extremes. They do not change
direction at CHoCH and can retain an old A across a long opposing move. This
demonstrates the need to connect direction changes before claiming a valid
historical hierarchy. No anchors or parameters were tuned to recover those
references. Counts and post-scan comparisons are in fractal_sequence_audit.json;
the four event files are named fractal_sequence_<timeframe>_<direction>.json.

## Literal pattern

- Bullish: A's high stays fixed while following candles fail to exceed it.
  The first candle C to exceed A's high confirms the lowest intervening low.
- Bearish: hold A's low fixed; the first later break below it confirms the
  highest intervening high.
- Require at least one intervening failed candle. Do not replace A with B's
  level or require a fixed price retracement, candle colour or inside bar.
- Wick crossing is valid; close beyond A adds a confirmation-quality flag.
- The reference extreme's original candle time is distinct from when it becomes
  knowable. Completed-candle implementation makes it available at C's close.
- Keep provenance for equal extreme candles rather than arbitrarily selecting
  a single origin when several tie.

## Diagnostic enumerator scope

The diagnostic enumerator allows each candle to start a possible A, keeping
older A candidates fixed at the same time. This preserves nested patterns and
does not choose a single controlling A or assign a structure hierarchy.
It is NOT a rule that a trader should act on all those patterns. In particular,
a break of B in a nested pattern does not confirm the still-unbroken original A.

Once two points have been confirmed on the active fractal sequence, the newer
one controls the next opposing fractal CHoCH. The user confirmed that breaking
a newer low at 150.30 can start the internal pullback while the older 150.00 low
holds, with no intervening internal BOS required. The sequential reset rule now
selects A within a supplied direction. Changing direction and initializing the
larger hierarchy remain separate from this diagnostic candidate pool.

Automatic selection of the active reference, trend phase, internal/swing hierarchy
and final POI eligibility is not implemented by this enumerator. Do not convert
all outputs into signals or treat their counts as trade counts.

If C also crosses the proposed opposite extreme in the same candle, ordering is
flagged for review. Quote gaps are retained as flags, not silently filled with
invented candles or automatically treated as trading filters. Candidate events
are computed on completed source candles; no exact intrabar detection time is
claimed from OHLC alone.

## Actual-sample comparison

The detector scanned all 6,043 M15 bars and all 1,465 complete H1 aggregates;
no reference price or expected pivot time was supplied to detection.
After detection, comparison with the four reference labels found each one:

| Reference | Source candle UTC | Price |
|---|---|---:|
| Jan 23 H1 POI-origin high | Jan 23 12:00 | 156.6000 |
| Jan 23 M15 liquidity high | Jan 23 13:15 | 156.3585 |
| Jan 29 H1 POI-origin high | Jan 29 01:00 | 155.7900 |
| Jan 29 M15 liquidity high | Jan 29 11:30 | 155.5225 |

Multiple A-level patterns can confirm the same extreme at different times.
The earliest fractal wick confirmation is not necessarily the internal or swing
close confirmation used for a POI. Matching a known extreme does not establish
correct hierarchy, trade eligibility or independent predictive performance.

Detailed outputs: fractal_candidates_15min.json, fractal_candidates_1h.json,
fractal_candidate_audit.json and fractal_reference_comparison.json.
