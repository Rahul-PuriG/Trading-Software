# Provisional connection from fractal CHoCH to internal pullbacks

Implemented in fractal_structure.py. Context mapping is restricted to 1H/4H;
M15 is rejected. The user's M15 LC-1 highs/lows serve as inducement near/inside
the POI; exact automatic liquidity selection remains unfinished. The combined structure suite has 54 passing tests, with
18 additional LC-1 qualification/sequence tests passing (72 total). No broker orders are submitted.

## Timeframe correction supersedes the earlier mixed comparison

The prior three-of-four comparison combined H1 context origins with M15 LC-1
liquidity points. The user clarified that these use different structure rules.
That combined validation claim is withdrawn. Original mixed reports/figures are
retained as historical diagnostics with superseded applicability labels.
Current context-only comparisons are in context_structure_audit.json. No 4H
aggregation anchor has been inferred from the 15-minute input series.

## Confirmed outside-sequence ordering

For the bullish newly forming A/B/C point, A-high first then B-low means fractal
CHoCH. B-low first then A-high means no fractal break from that newly forming
point. The bearish construction mirrors this. This does not suppress an
independent break of a previously confirmed protected reference.

The mapper accepts complete one-minute evidence for the source candle, verifies
its timestamps and aggregate OHLC, and observes which level is first crossed.
Missing data, a mismatching feed, first crossings within one minute, or additional
uncertain reversals remain review-required. With low-first ordering, the swept
B point is not promoted as a newly protected reference. With high-first ordering,
the context direction reverses. Source-bar state is still available at source
close; the observed minute times are not a claim of an incremental intrabar engine.

## Confirmed rules applied

- Track the user-confirmed directional A advance/freeze/reset sequence.
- The newer confirmed low/high becomes the opposing fractal-break reference.
- Wick crossing qualifies; an equal touch does not. Close confirmation adds
  quality without making a wick invalid.
- A qualifying opposing break changes fractal direction. When connected to the
  internal tracker, it starts the internal pullback without automatically
  reversing internal direction. Internal reversal still requires a close through
  its own protected boundary.
- A reference's older origin time remains distinct from its availability time.

## Implementation conventions still requiring chart validation

The initial direction and first source candle are supplied. On an unambiguous
CHoCH, the preceding leg extreme becomes the opposite reference, known at the
CHoCH candle close, and the CHoCH candle seeds the new directional A sequence.
These linking conventions are explicit implementation choices, not additional
rules the user has independently confirmed.

The source-candle implementation does not claim exact intrabar CHoCH timestamps.
Outside newly forming points can now use the confirmed ordering policy above.
Other ambiguity, including a source candle that crosses an already protected
reference and makes a new leg extreme, still stops with review_required. Missing
source intervals are retained; input coverage remains a caller responsibility.

Optional integration with InternalPullbackTracker requires the same source
duration and supplied initial internal boundaries. Only completed, unambiguous
source candles feed that tracker. Initial swing boundaries, phase/range mapping,
POI eligibility and LC qualification remain separate.

## Historical mixed-timeframe comparison — superseded

Calendar-day windows start at UTC midnight on Jan 23 and Jan 29, independently
with both BUY and SELL initial directions. Expected prices and pivot times were
not supplied to detection. Matching occurs only after the trace, against the
existing four reference labels. These window starts and directions are explicit
initialization inputs, not automatic historical initialization.

| Reference | Result in the supplied daily windows |
|---|---|
| Jan 23 H1 origin high 156.6000 | Matched; available 14:00 UTC with either starting direction |
| Jan 29 H1 origin high 155.7900 | Matched; available 04:00 UTC with supplied SELL start |
| Jan 29 M15 liquidity high 155.5225 | Matched as a turning reference at 13:15 UTC with supplied SELL start |
| Jan 23 M15 liquidity high 156.3585 | Unmatched; needs further classification/reconciliation |

The M15 rows above are LC-1 annotations, not valid targets for this 1H/4H context
mapper. Their match/mismatch cannot validate either algorithm. H1 extrema still
require hierarchy/POI validation. The Jan 29 H1 fractal availability is earlier
than its annotated internal-break confirmation; the two must remain distinct.

Both M15 Jan 23 daily traces and all four H1 daily traces process their full
selected days. The Jan 29 M15 BUY-start trace stops at 00:45 UTC; the SELL-start
trace stops at 19:30 UTC, the reviewed LC candle. Whole-context traces from
November stop earlier at outside candles, so they do not reproduce the January
references as a continuous historical map. See fractal_structure_audit.json
and the twelve fractal_structure_<frame>_<window>_<direction>.json trace files.

## Earlier M15 ordering illustration — not the LC-1 structure rule

Jan 29 M15 A starts 19:00 UTC, high 155.4925. B starts 19:15 UTC, low 155.281.
C starts 19:30 UTC, high 155.612 and low 155.209: it breaks both A's high and
B's proposed fractal-low reference. On the uploaded one-minute midpoint data,
the first A-high crossing occurs in 19:30, and the first B-low crossing occurs
in 19:40. The aggregate M15 OHLC alone does not establish this order.

The user has now confirmed the high-first/low-first distinction while correcting
the timeframe: apply context-fractal structure on 4H/1H. This M15 chart remains
an illustration of chronological crossings only. It is not an implementation or
validation of the user's different M15 LC-1 use of fractal CHoCH.
