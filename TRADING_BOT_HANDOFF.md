# Trading bot handoff — 2026-11-01

## Latest update — automatic LC-1 connection
The full Python suite now passes 136 tests. New uncommitted work after 4d5484e:
swing_lc1.scan_lc1_candidates, check_lc1_discovery.py, test_lc1_candidates.py and
README changes. The older Git bundle alone does NOT include these changes;
the archive includes their current readable files. Copy those files over the
bundle-restored checkout before continuing.
Read data/strategy_review/LC1_DISCOVERY_CONNECTION.md and the automatic connection
JSON. With supplied H1 zones/context, automatic M15 inducement discovery produces
the expected first Jan23 and Jan29 signals/fills (Jan23 one amendment, Jan29 zero).
An old POI touch no longer automatically authorizes an outside-POI LC candle;
that case requires review. Duplicate support pairs/signals are merged and
pre-window consumed points are excluded under a provisional freshness policy.
Extra Jan23 candidates (six raw signals across the later sample versus Jan29 one)
need changing context, reentry and position-lifecycle validation. They are NOT
confirmed trades. Next work is dynamic context/POI and position integration,
not another general proximity or PBID question; those rules are already resolved.

## Project status
User is building an IBKR USDJPY swing trading bot. Rules and components exist;
NO full automated USDJPY strategy backtest has been completed. Do not confuse
passing unit tests or selected examples with strategy profitability.

Repository: https://github.com/Rahul-PuriG/Trading-Software.git
Working branch: work
Latest commit: 4d5484efd6b23766d29b24b4c74c17197c398e45
Commit message: Add USDJPY strategy research components
All 129 Python tests passed at that commit. Later uncommitted changes are included
as readable source files in this archive; see the latest update below.
GitHub PUSH FAILED: network proxy HTTP 503; managed environment reported
Tailscale enrollment failure and blocked non-platform egress. The work is
committed locally and backed up in the included Git bundle, NOT confirmed pushed.
Do not change/publish environment settings just to retry this failed push.

## Restore
The Git bundle contains the complete tracked repository history and work branch.
Clone it using: git clone -b work trading-software-work.bundle Trading-Software
The archive also contains readable traiding-bot source files. Its spelling is
intentional and matches the user's existing folder name.
Copy the private traiding-bot/data folder into the restored repository. Git does
not restore that folder because data/, reports/ and logs/ are ignored.
original_uploads/ preserves files present in the old attachments workspace;
generated_images/ preserves locally available generated explanatory images.
Old absolute /workspace/attachments paths in scripts/documents may need to be
replaced with the restored files. Do not assume uploaded-file IDs or the old
cloud environment are accessible from a new chat.

This is a file/research handoff, not a full chat export. Inline chat-only images,
messages, connected app state, credentials and running sessions are not restored.

## Read first
traiding-bot/data/strategy_review/CURRENT_SPEC.md
traiding-bot/data/strategy_review/USER_CLARIFICATIONS.md (chronological; latest wins)
traiding-bot/data/strategy_review/INDUCEMENT_DISCOVERY.md
traiding-bot/data/strategy_review/LC1_IMPLEMENTATION.md
traiding-bot/README.md

The private data directory includes journal records, teaching diagrams/charts,
original review notes, selected-case replays, market CSVs and audit artifacts.
Keep private journals/charts/strategy documents out of GitHub unless explicitly
authorized. The code push did not include them.

## Latest confirmed rules
- USDJPY; daily narrative; 4H/1H context/POIs, with more weight on 4H.
- Context fractal/internal/swing hierarchy is on 4H/1H. M15 is entry execution.
- Internal/swing breaks require a close; context fractal wick breaks qualify.
- Fractal A stays fixed after first failed candle until C breaks original A.
  Retain intervening lowest low/highest high. C seeds next A; advance A with
  higher highs/lower lows before the next failure. Outside-bar order matters:
  bullish high-first then low = CHoCH; low-first then high = no break from the
  newly forming point. Unresolved within-minute order remains review-required.
- Opposing context fractal CHoCH starts internal pullback, not internal reversal.
  Restored fractal alignment leaves a candidate internal pivot; internal BOS
  close beyond the prior internal extreme confirms it. Fib .36-.5 is a soft
  preference, not an admission filter.
- POI = ONE selected full high-low candle including wicks; color irrelevant.
  Must cause confirmed structure break and initially be unmitigated. Multiple
  POIs, including mid-leg zones, are allowed. Touch mitigates but need not
  invalidate. Any price crossing the far boundary invalidates immediately.
- M15 inducement is liquidity for LC-1, NOT the HTF context-fractal trend map.
  Selected sell high must cause a prior M15 low break; buy low mirrors through
  prior M15 high. Wick is sufficient, close adds quality.
- ANY qualifying inducement may be used. No newest-only, extreme-only,
  left-leg-only, formation-type or no-PBID-to-the-right rejection filter.
- IMPORTANT latest correction: near/inside POI improves QUALITY, not eligibility.
  NO maximum-distance filter. Detect inducement ONLY on entry timeframe M15.
  Do not invent a numerical proximity score or automatically label it HIGH.
- Valid POI mitigation + qualifying liquidity sweep + valid closed M15 LC candle
  are required. Buy stop at candle high, loss stop at low; sells mirrored.
  No buffers. Unfilled entry AND stop amend together; recalculate size.
  Filled trade has fixed stop and 2R target. Reentry needs a new valid setup.
- Account USD10,000, 50:1 leverage; each independent trade risks 1% of available
  funds/free margin. Concurrent valid trades allowed. Gross-margin approximation.
- Initial test filters OFF: session restriction, two-loss daily cutoff, news.
- Costs provisional: 1 pip spread, .1 pip adverse stop/market slippage,
  commission max($2, notional * .00002) per fill. No overnight financing.

## Data and validation
Validated private paths relative to traiding-bot:
data/strategy_review/usdjpy_sample_audit/USDJPY_context_15min.csv
data/strategy_review/usdjpy_sample_audit/USDJPY_execution_1min_v2.csv
Use the v2 minute CSV: 9,975 rows. Original non-v2 minute CSV is incomplete.
All 665 overlapping M15 bars match minute aggregation exactly. Source IBKR
midpoint; journal screenshots OANDA/FXReplay, so differences remain possible.
User-facing chart/reference times: America/Halifax, not New York. CSV uses UTC.

109 manual journal rows and 321 chart links were recovered. Recorded outcomes
are manual journal results, not a new backtest. Only a representative subset
of charts has been visually reviewed; do not claim all images were validated.
Jan 23 and Jan 29 2025 have conditional reference reconcilations using annotated
zones/context. Jan 23 order amends before fill; Jan 29 no amendment before fill.
No real strategy orders were placed by research modules.

inducement_candidates.py independently scans 6,043 M15 bars and finds both
marked January inducement origins. 37,905 origin/prior support pairs represent
4,165 distinct side/origin/price points; NOT trades. 13,456 pair cases need
ordering review. 33 generated pairs match the selected-reference qualifier.
Historical mixed M15-context-fractal comparisons are explicitly superseded.

## Important modules
swing_lc1.py: selected M15 inducement qualification, sweep/POI/closed candle,
  pending amendments; requires annotated context/zone inputs.
inducement_candidates.py: automatic raw M15 candidate pair enumeration.
fractal_candidates.py, fractal_structure.py, internal_structure.py,
  structure_evidence.py: structure stages, conditional initialization and flags.
fx_account.py, reference_replay.py, check_swing_reference.py: account/execution
  and two selected-case reconciliations.
download_usdjpy_sample.py: read-only local TWS data downloader.
bot.py: existing local Windows IBKR paper CLI; separate from strategy detection.
backtest.py/risk_backtest.py: earlier SPY SMA experiments, not the USDJPY plan.

## Resume work
No full strategy backtest exists yet. Remaining work includes automatic HTF
hierarchy initialization/POI discovery, candidate lifecycle and deduplication,
connecting M15 candidates to context/POI/entry handling, LC-2A/2B detection,
resolving remaining intrabar/replacement cases, and journal validation. Proximity
is NOT an unresolved hard filter; user already explicitly resolved it as quality.
Do not ask the user to reupload charts already present in this archive.

From traiding-bot, run:
python -m unittest discover -q
python check_swing_reference.py --context data/strategy_review/usdjpy_sample_audit/USDJPY_context_15min.csv --minutes data/strategy_review/usdjpy_sample_audit/USDJPY_execution_1min_v2.csv
Install requirements.txt if dependencies are missing. Prior interpreter was
/workspace/trading-bot-venv/bin/python; that environment may not exist after restore.

## Latest user POI-selection images
Read traiding-bot/data/strategy_review/POI_SELECTION_FROM_IMAGES.md. POIs come
from the left leg that produced the break: the origin extreme, and additional
mid-leg sweep-backed origins (x). More than two zones are allowed. More extreme
and sweep-backed improve quality, without an extreme-only restriction or an
automatic HIGH grade. Retain the single full-range candle, confirmed break and
freshness requirements. This is HTF POI selection, separate from M15 entry
inducement. The inline image binaries are not in the workspace; their content
is recorded in these notes. No automatic POI detector has yet been implemented.

## Latest update: conditional HTF POI origin discovery
poi_mapping.py and test_poi_mapping.py are now included as uncommitted source.
Full Python suite: 146 passing tests. Read POI_MAPPING_STAGE.md in the private
strategy_review folder. The detector discovers both marked January H1 origins
without their target origin times/ranges as inputs, but internal reference levels
and mapping windows remain annotated. Freshness uses a provisional M15 closed-
departure convention; candidates are not automatically active/tradable zones.
The Jan29 scan also emits the next 02:00 UTC candle inside the marked 01:00
origin. A/B chart poi_origin_A_B_review.png asks whether B qualifies separately;
that user clarification is pending. No extra zone is silently accepted.

## A/B review resolved — latest user answer
User selected A, not B. The mapper keeps the marked Jan29 01:00 UTC origin and
records the next contained 02:00 candle in excluded_candidates linked to A.
The implementation treats the immediately adjacent contained unswept local
candidate as the same origin, narrowly for the same break/window. It is not
a universal nesting or midleg-POI ban. Both January origins still match.
Full suite: 148 passing tests. Read POI_MAPPING_STAGE.md and latest
USER_CLARIFICATIONS.md. The A/B chart is the original question, now resolved.
