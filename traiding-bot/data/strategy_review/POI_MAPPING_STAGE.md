# Conditional HTF POI origin discovery

Implemented in poi_mapping.py. Twelve tests pass; the full Python suite passes
148 tests. No broker connection, orders, numeric grading or profitability claim.

## Inputs and discovered output

Supply 1H or 4H candles, M15 observation bars, an available internal/swing break
reference, and optionally a mapping-window start. The source origin timestamp,
zone range and desired signal time are not inputs. A body close through the
supplied reference confirms the mapping window; a wick alone is insufficient.

Discover the window extreme as one source, plus other locally break-supported
source candidates from the diagnostic HTF candle-pattern pool. Keep separate
full candle ranges and multiple candidates. Do not use candle color, a one/two
zone maximum, an extreme-only restriction or a numeric grade cutoff.

Report earlier-known HTF reference points taken by an origin candle as sweep
evidence. This is a POI confluence check, separate from the M15-only LC-1
inducement scanner. Local raw pattern support is not a final internal/swing
classification. Mid-leg candidates without proven sweeps are retained for
other-confluence review, not declared automatically good or invalid.

All output zones require mapping validation. Supplied reference levels/window
boundaries still encode human structure selection. Phase, narrative, active
POI admission and final entry/portfolio integration remain unfinished.

## Provisional freshness audit

After the source candle ends, a M15 close outside its near edge establishes an
observed departure. A later wick overlap is an observed return before structure
confirmation. A far-edge breach is invalidation. Missing coverage is flagged.

Initial overlap while the move forms is not automatically called mitigation.
This departure convention is an explicit implementation choice requiring chart
validation, not a newly user-confirmed rule. The algorithm cannot resolve all
departure/retest ordering within a single M15 candle. Consequently its freshness
status is evidence, not independent proof that a zone can be traded.

## Actual H1 reference comparison

The supplied reference for Jan 23 is the 09:00 UTC H1 low 156.3505, known at
10:00 UTC. Jan 29 uses the Jan 28 14:00 H1 low 155.050, known at 15:00 UTC.
Both reference levels and their scale/window are annotated; no expected origin
was supplied to detection. Comparison is performed after all mapping.

| Reference | Discovered source UTC | Full range | Available after internal break |
|---|---|---|---|
| Jan 23 marked origin | Jan 23 12:00 | 156.372–156.600 | Jan 23 14:00 UTC |
| Jan 29 marked origin | Jan 29 01:00 | 155.592–155.790 | Jan 29 06:00 UTC |

Both have observed departures with no subsequent return before confirmation
under the stated M15 convention. Both are extremes of their supplied windows.
This verifies these selected origin matches, not a full automatic hierarchy.

The initial scan also emitted the next H1 candle, 02:00 UTC, range
155.5925–155.7840. It is contained inside the marked source candle, has local
break support and no proven sweep in this scan. The user explicitly chose A,
not B. The revised scan preserves B as an excluded same-origin candidate linked
to A. It retains one candidate for each of the two reviewed January references.

The implementation applies that distinction narrowly to an immediately adjacent
contained local candidate without independent sweep evidence beside a leg
extreme, for the same break/window. Do not generalize it into a ban on separate
mid-leg origins, independently sweep-backed sources or 4H/1H nested zones.
More general overlap/formation patterns still require validation. This choice
comes from the user's review, not the trade's recorded outcome. The A/B chart
shows the original review question; its resolution is recorded here.

## Artifacts

poi_origin_mapping_audit.json contains outputs and post-mapping comparisons.
poi_origin_A_B_review.png shows the one specific ambiguous candle choice.
No original user's inline image binaries were modified.
