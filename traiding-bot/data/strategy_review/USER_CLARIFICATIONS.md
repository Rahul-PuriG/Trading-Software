# User clarifications — USDJPY swing plan

Recorded 2026-11-01. These clarifications take precedence over conflicting
timeframe mappings in the export. No executable strategy has been created.

## Confirmed

- Daily (1D): higher-timeframe narrative.
- 4H: medium-timeframe immediate bias.
- 1H: may replace 4H for immediate bias when 4H is too noisy. The switch criterion
  is not yet defined; do not switch retrospectively based on trade outcome.
- 15-minute: entry timeframe.
- User lives in Antigonish, Nova Scotia and uses local time to coordinate with
  international sessions. Use IANA America/Halifax, with daylight-saving changes.
  Do not treat the timezone as fixed UTC-4 or UTC-3 year round.
- No stop-loss buffer for now. Exact stop anchor still needs confirmation.
- User describes entry as the high/low of a closed candle satisfying the conditions.
  Confirm a buy-stop at high / sell-stop at low, rather than market entry at close,
  and confirm that no entry buffer applies.
- All three journals are manual historical backtests. User states core rules did
  not change, but each round cut down more "noise." Which candidates were excluded,
  whether exclusion criteria were knowable before entry, and whether the same
  filters were applied to earlier rounds need clarification. Do not automatically
  treat the rounds as identically filtered samples or independent validation.

## Still unresolved

1. Buy stop at qualifying candle high, sell stop at its low, with no entry buffer?
2. Initial protective stop at opposite extreme of that same candle, with no buffer?
3. Objective condition for switching 4H to 1H, and whether POI selection switches too.
4. Exact permitted session windows in America/Halifax; year-round fixed local
   windows versus following international session clock/DST changes.
5. Definition/examples of noise filters and whether they apply to all rounds.
6. Early invalidation, structure/zone/liquidity rules and order amendment rules.
7. Fixed 2R target and enabled setups remain as in the source pending any correction.

Ask only a few questions at a time. No backtest or order execution until the
applicable rules have been made precise and confirmed.

## Follow-up confirmations (supersede corresponding open items above)

- User confirmed: after a qualifying 15-minute candle closes, buy-stop at its
  high with protective stop at its low, or sell-stop at its low with protective
  stop at its high. Neither entry nor initial stop has a buffer.
- User recorded trades across every session and has not specified restricted
  hours. First-test interpretation: no session admission filter; retain local
  timestamps/session labels for later analysis. Recorded trade times alone do
  not define an eligibility window. News and daily-loss restrictions remain
  separate rules and are not removed by unrestricted sessions.
- User switches from 4H when momentum is weaker and no clear trend is developing,
  provided 1H shows a clear trend. User tries to exclude countertrend trades.
  These are currently discretionary descriptions, not numerical conditions.
- Need to confirm trend definition (e.g. structure rather than an assumed moving
  average), which timeframe's trend governs eligibility, whether daily alignment
  is mandatory, and whether switching bias also switches POI/zone timeframe.
- Need confirmed swing-identification and close-vs-wick break rules before coding
  any structure-based trend detector; HH/HL language alone does not resolve this.

## Trend and POI clarifications

- A clear trend means the larger swing trend and the internal trend inside its
  swing legs point in the same direction. These are two levels of structure,
  not moving-average proxies. How their pivots and breaks are identified remains
  to be defined using the user's method.
- Daily shows the larger moves/context. Agreement with daily trend is NOT a
  mandatory trade filter. Trade narrative and POI selection use 4H or 1H.
- 4H has more weight than 1H. A 1H POI may be selected when it has everything
  required by the user's POI criteria. Nesting/alignment of 1H and 4H POIs is
  the preferred case, not stated to be mandatory.
- Do not implement an automatic 4H/1H switching rule, a minimum score, or a hard
  nesting requirement until the user's qualification/priority rules are clear.
- Still need: definition of outer swing versus internal pivots, pivot confirmation
  timing, close/wick break requirement, exact POI boundaries and freshness,
  handling of opposing 4H/1H structures, and the early-invalidation method.

## Structure confirmation and opposing bias

- User defines swing turning points through a change in direction of internal
  structure: the high/low is identified according to where the internal reversal
  occurs. Do not substitute an arbitrary fixed-bar fractal detector.
- A candle close beyond the relevant level is mandatory to confirm both swing
  and internal structure breaks. A wick alone is insufficient.
- A clearly bearish 4H blocks a bullish 1H trade; user waits rather than buying
  against that 4H bias. A symmetric bullish-4H/short restriction has not yet been
  explicitly confirmed, though it would be consistent with the described approach.
- Internal-reversal confirmation must be recorded at the actual confirmation
  candle, not retroactively at an earlier extreme. Exact internal pivot selection
  and the extreme used as the swing endpoint still need an annotated example.
- Next priorities: supply/demand POI candle selection and price boundaries;
  freshness/mitigation and failure rules; early invalidation definition. No
  automated structure detector or backtest has been implemented for this plan.

## POI range and early invalidation — partial clarification

- User marks the POI candle's entire high-to-low range, including wicks.
  Which candle is selected to originate the zone remains unresolved.
- For LC-1 and LC-2A, user describes early invalidation as left-hand inducement
  already taken, followed by a consecutive candle crossing a high/low before
  the POI is hit: the setup did its expected actions too early, before mitigation.
- Preserve this as a sequence-dependent rule, not a generic zone-break rule.
  The exact crossed reference (liquidation candle versus another structure),
  direction for buys/sells, and close-versus-wick trigger have NOT been confirmed.
- Do not apply the previously confirmed candle-close requirement for structure
  breaks automatically to early invalidation; ask whether it also applies here.
- Need one chronological buy example: zone bounds, liquidity level swept,
  liquidation candle bounds, next candle bounds, and first POI touch. No detection
  code should be written from the ambiguous wording alone.

## Early invalidation — buy direction confirmed

- Applies to LC-1 and LC-2A per the user's clarification.
- After the relevant inducement has been taken, and BEFORE the demand POI is
  touched, the next candle breaking ABOVE the liquidation candle HIGH invalidates
  the BUY setup. User explicitly selected the above-high interpretation.
- A wick is sufficient; a candle close is not required for this invalidation.
  Keep this separate from structure-break confirmation, which requires a close.
- Mirrored SELL rule (next candle below liquidation-candle low before supply
  mitigation) has not yet been confirmed; do not silently infer it.
- Still unresolved: whether only the immediately next candle or later pre-touch
  candles can invalidate; exact inducement/liquidation identification; event
  ordering if POI touch and early-invalidation level occur in the same data bar.
  Obtain lower-timeframe sequencing or flag ambiguity rather than assume the
  favorable ordering. Zone-origin candle selection is also still unresolved.

## Sell invalidation and POI qualification confirmed

- User confirmed the mirrored SELL rule: after inducement is taken, a next-candle
  wick BELOW the liquidation candle LOW before the supply POI is touched invalidates
  the setup. No close is required for this early-invalidation condition.
- User restated the POI checklist: structure break (CHoCH/i-BOS/BOS) and
  unmitigated are mandatory. Other listed confluences remain quality criteria;
  do not mark all as required or impose a score cutoff without confirmation.
- This checklist does not identify the origin candle or base-candle group whose
  high/low defines the POI. Continue to ask for the exact candle selection or an
  annotated example rather than assume the last opposite-colour candle.

## POI candle and multiple-zone selection

- User confirmed that each POI is ONE selected candle's full high-low range,
  including wicks. Candle colour does not matter; do not use a last-opposite-colour
  heuristic. This supersedes earlier uncertainty about single versus base-group candles.
- If multiple candles within a leg qualify, keep them as separate valid POIs.
- A POI need not be at the leg's extreme. The user also marks qualifying mid-leg
  candles, particularly in a strong trending move where an extreme retest is
  considered less likely. An extreme-only restriction would misrepresent the plan.
- Strong-trend/depth preference is currently qualitative. Do not assume a numerical
  momentum threshold, require a mid-leg zone, or mark all leg candles as POIs.
- Still need reproducible qualification for each candidate candle, first-touch /
  mitigation lifecycle, and whether entries are accepted at any qualifying POI
  or subject to an additional zone priority when several remain valid.

## Fractal CHoCH and countertrend setup eligibility

- User distinguishes THREE scales: fractal (immediate/smallest), internal, and swing.
- A fractal CHoCH is the first immediate structure-direction change, smaller
  than internal or swing reversal. Exact pivot selection at each scale remains
  unresolved; do not replace it with arbitrary lookbacks.
- At a qualifying POI, a fractal structure change can support a valid setup even
  when BOTH internal and swing oppose the trade. User labels the ordinary case
  LOW probability and may still take it.
- Do NOT universally exclude low-probability / phase-D trades or require internal
  and swing alignment for every entry. This qualifies the earlier preference
  to wait when 4H clearly opposes the proposed trade.
- User also describes an initially very bullish/bearish market reversing with
  strong momentum and an immediate CHoCH. Such a reversal may be graded HIGH
  probability while larger structures still oppose it. The precise pre-entry
  evidence distinguishing this case from ordinary LP is not yet defined.
- Keep setup validity, structure alignment, and probability grading separate.
  Do not infer quality from whether the trade later won.
- Round 1 row 4, January 3, 2023: user's explanation supports validity as a
  countertrend fractal-change setup, graded low because larger structures oppose it.

## Phase diagram authority

- User explicitly supplied the MTF phase diagram as guidance for when to take
  each phase; its text has been reviewed and transcribed into PHASE_RULES.md.
- Use its contextual distinctions rather than ask the user to restate them or
  invent a generic strong-momentum threshold.
- A aligns swing/internal; B follows swing against internal; C follows internal
  against swing; D opposes both. Diagram gives different mitigation/confirmation
  guidance for each, plus range-edge guidance.
- D is aggressive with at least M15 CHoCH if traded, not an automatic high-quality
  setup merely because a fractal reversal is present. See full conditional wording
  and the user's journal exception in PHASE_RULES.md.

## POI lifecycle, pending orders and re-entry

- A 15-minute wick touch is enough to mark a POI mitigated; a body/close touch
  also counts. Mitigation is not automatically invalidation or deletion.
- If the POI becomes invalid before an LC setup appears, remove it and do not
  trade from it. The exact price-based invalidation trigger is still unresolved:
  the user did not specify wick-through versus close-through of the far boundary.
- When an unfilled entry is moved to the next qualifying closed 15-minute
  candle's high/low, move the protective stop to that candle's opposite extreme
  as well and recalculate size to maintain the 1% risk budget.
- These amendments apply BEFORE fill. Do not trail the stop after entry; the
  user's management rule remains fixed stop and 2R, no partial exits.
- A stopped-out trade does not automatically invalidate the POI. Re-entry is
  allowed while the POI remains valid AND a fresh valid setup appears. Daily
  two-loss restriction remains applicable; do not re-enter on an old signal.
- The supplied LC diagrams say pending-entry adjustments continue while price
  remains within the MTF POI. Exact expiry/cancellation on leaving the zone,
  the distinction between a permitted sweep and zone failure, and whether
  replacement entries must move only toward price remain unresolved.
- Source "unmitigated mandatory" is understood as fresh-zone selection followed
  by a tradeable mitigation state, not a ban on all touched-zone setups. Repeated
  attempts are explicitly permitted while valid. The POI lifecycle must represent
  these states separately.

## POI invalidation — immediate boundary breach

- User confirmed that price passing through a POI invalidates it immediately;
  no candle close is required on any timeframe.
- Operational interpretation: demand fails when price trades below the zone's
  low; supply fails when price trades above its high. A wick breach suffices.
  Merely touching the near boundary is mitigation, not far-boundary invalidation.
- Remove the invalid POI from future setup eligibility. Any pending entry tied
  to it must be cancelled rather than amended or reused. This cancellation is
  the implementation consequence of no trading from an invalid zone.
- Exact equality at the far boundary is not explicitly specified; the confirmed
  language is "passes/crosses through," not an invented extra pip buffer.
- When historical data shows a possible entry and far-boundary failure in the
  same bar, use lower-timeframe event sequencing or flag ambiguity; do not give
  the entry favorable precedence just from OHLC.
- This defines zone eligibility; treatment of already-filled trades remains
  governed by the confirmed protective stop and target unless user changes it.

## Initial-backtest filter overrides

- User explicitly disabled the maximum-two-losses-per-day rule for now.
  Do not stop entries or re-entries based on daily realized losses in this test.
- User explicitly disabled the high-impact-news exclusion filter for now.
  Do not exclude entries within 30 minutes before news or introduce an unconfirmed
  post-news blackout. No economic-calendar download is required for this version.
- Session eligibility is also unrestricted per the earlier clarification.
- Keep 1% planned risk per trade, fixed 2R target, qualifying POI/phase/LC rules,
  immediate zone invalidation and confirmed pending-order/re-entry behavior.
- These overrides apply to the initial test, not an assertion that the original
  written plan omitted these restrictions. Label the resulting report accordingly.

## Concurrent trades and sizing base — partial clarification

- User permits another concurrent USDJPY trade if it independently meets the
  setup rules. Do not impose a one-open-position restriction.
- User specifies sizing from "remaining 1% of balance." Exact denominator still
  needs confirmation: realized account balance, equity including open P&L, or
  available funds/free margin after existing exposure.
- Do not silently deduct the first trade's stop-risk budget from account balance:
  risk reservation, cash deployment, margin usage and realized losses are distinct.
- Do not infer a shared 1% cap for all open trades or unrestricted leverage.
  Validate sizing basis, margin model and available capacity before a cash/P&L
  simulation. Concurrent trades will require separate trade IDs and stops/targets
  even though the broker may report a net position per currency pair.

## Concurrent sizing denominator confirmed

- User selected AVAILABLE FUNDS / FREE MARGIN as the risk-sizing denominator.
- Each independently valid new trade budgets 1% of then-available funds after
  existing positions' margin usage, not 1% of original capital or a shared cap.
- This overrides any earlier assumption of realized-balance or equity-only sizing.
- Required modelling inputs still missing: starting funds/account currency and
  margin/leverage method. Specify treatment of open P&L in available funds and
  account for currency conversion and netting before claiming broker equivalence.
- Never approximate available funds by simply subtracting prior trades' stop-risk
  budgets. Margin capacity and potential loss are different quantities.

## Initial capital and leverage confirmed

- User accepted starting capital of USD 10,000 and selected fixed 50:1 leverage
  as the historical simulation assumption. Initial margin rate is 2% of USD
  notional before account-specific adjustments; do not claim this is verified
  IBKR margin policy or permission for live leverage.
- Risk budget for each new independently valid setup: 0.01 * then-available funds.
- USDJPY position units are USD base units; pip value and stop P&L require
  conversion from JPY to USD using the applicable exchange rate. Fixed leverage
  does not imply 1% stop risk equals 1% of notional or margin.
- Free-margin calculation conventions (open P&L, gross versus broker-netted
  exposures), spread, commission, swaps, stop-out handling and lot increments
  remain modelling details to specify. No actual USDJPY backtest has yet been run.

## Provisional transaction-cost modelling — not broker-verified

- User does not know USDJPY spread or commission. Record estimates as provisional
  modelling assumptions, not user-observed charges or current IBKR pricing.
- Proposed baseline total bid-ask spread: 1.0 JPY pip (USDJPY pip = 0.01 JPY).
  When using midpoint OHLC, synthesize bid/ask at midpoint +/- half the spread.
  Do not apply the spread again if the data already supplies bid and ask prices.
- Proposed commission per entry/exit fill: max(USD 2, USD notional * 0.00002),
  i.e. 0.2 basis points with USD 2 minimum per order. This is an explicit
  illustrative fee model, not an assertion of the user's broker schedule.
- Proposed additional adverse slippage: 0.1 pip per stop/market fill; no adverse
  fill below/above a limit order's protected price. Gaps use actual available
  opening-side prices, not an assumed guaranteed stop level.
- Spread sensitivity runs: 0.5, 1.0, 2.0 pips with the same commission/slippage
  model; zero-cost output only as a diagnostic, never a realistic case.
- Historical swaps/rollover financing are unknown. Initial results must be
  labelled AFTER MODELLED TRADING COSTS, BEFORE OVERNIGHT FINANCING and taxes.
  Do not claim fully net profitability for a swing strategy while swaps are absent.
- Reports must include exposure/holding duration and separate cost components
  so financing can be added later. No USDJPY cost-sensitive backtest has yet run.

## Journal dates confirmed and timestamp exception

- User corrected Round 2 Trades row 13 from 2025-08-11 to 2024-08-11.
- User confirmed Round 3 Trades row 18 `01/06/25` means 2025-06-01.
- Applied only to journal_records.csv and audit overrides; original XLSX files
  are unchanged. Full provenance is in date_corrections.json.
- Round 2 row 13 still records time 10:15:00. Corrected date 2024-08-11 is Sunday;
  10:15 AM America/Halifax is outside the usual FX trading week. Its supplied
  M15 chart shows activity around the Sunday-to-Monday reopening period.
  Verify AM/PM or original chart timezone rather than silently shift the trade.

## Timestamp exception resolved

- User explicitly confirmed Round 2 row 13 as August 11, 2024 at 10:15 PM
  (22:15) Antigonish local time, America/Halifax.
- This is 2024-08-11T22:15:00-03:00, equivalent to 2024-08-12T01:15:00+00:00.
- Corrected working journal and audit provenance. Original XLSX remains unchanged.
- The original 10:15:00 value is retained in date_corrections.json; this correction
  does not change other trades' timestamps or establish the chart display timezone.

## Uploaded USDJPY sample audit

- User uploaded metadata, 6,043 context 15-minute bars and 3,495 execution
  one-minute bars from IBKR IDEALPRO MIDPOINT. All timestamps sorted and unique;
  OHLC values passed basic validation.
- Execution coverage FAILED: 9,975 minute slots are implied by downloaded
  context bars in the execution range, but 6,480 are absent from the one-minute
  file. Repeated 18h16m gaps omit both journal entry windows. Do not replay trades
  through these gaps or publish strategy results from this sample.
- Original downloader used one-day requests ending at local midnight and did
  not enforce cross-timeframe coverage. Version 2 uses explicit 14,400-second
  windows and requires minute coverage to match the downloaded context bars.
  This reference check does not independently certify complete context coverage.
- Six downloader tests pass, including partial-session rejection. Actual corrected
  IBKR download must be run locally; it has not yet been verified.
- Preliminary 15-minute reference matching: January 23 at 14:30 UTC has high
  156.405 / low 156.322, matching chart labels. January 29 at 19:30 UTC has high
  155.612 / low 155.209, about 0.1 pip from chart labels 155.613 / 155.208.
  These are candidate candle matches, not automated setup detection.
- January 29 journal time 15:30 local matches the candidate liquidation candle
  START; under the closed-candle rule an entry based on it cannot be placed until
  15:45 local. Do not treat every journal entry timestamp as an exact fill time.
- Source copies, hashes and findings are saved under usdjpy_sample_audit/.

## Corrected USDJPY sample and reference replay

- Uploaded downloader-v2 sample contains 9,975 one-minute bars, no duplicates,
  valid OHLC, zero missing/unexpected minute slots relative to context coverage.
- All 665 overlapping 15-minute bars reconstructed exactly from minutes:
  max open/high/low/close differences are all zero. This validates internal
  sample consistency, not an independent exchange calendar or OANDA equivalence.
- Reference replay uses two manually identified candidate M15 signal candles,
  not automatic POI/phase/LC detection. No pending-order amendments were needed
  in the initial entry windows of these cases. No account sizing or net performance
  was calculated. Commissions and financing are excluded from this price-path check.
- Jan 23 candidate signal starts 10:30 Halifax, closes 10:45. Short triggers in
  the 10:51 minute. Under assumed total spread 1 pip and market slippage 0.1 pip,
  entry 156.321, stop price 156.405 (model stop fill 156.406), target 156.153;
  stop occurs in 11:23 minute. Zero-spread/slippage diagnostic instead reaches
  target 156.156 in 11:09 minute. Price-side modelling materially changes outcome.
- Jan 29 candidate signal starts 15:30 Halifax, closes 15:45. Short triggers in
  15:51 minute. Assumed-cost price path: entry 155.208, stop 155.612, target 154.400;
  target reached 22:17 that day. Current no-buffer/2R reference path only; not a
  claim to recover every original journal execution detail.
- All times above are America/Halifax in January (UTC-4); minute-bar event times
  are not exact execution seconds. Daily quote gaps present in both timeframes
  are retained, and stop gaps are checked at the next available quote.
- Signal-bar starts, order activation and minute-level fills are distinct fields.
  Journal times may refer to different stages; do not retroactively enter at the
  signal candle's opening time. Source/audits are under usdjpy_sample_audit/ and
  reference_replay.json. Eleven downloader/replay tests pass.

## January 29 POI / LC candidate mapping for user review

- Mapped a plausible 1H origin candle starting 2025-01-29 01:00 UTC (Jan 28
  21:00 Halifax), full range 155.592–155.790, from the IBKR sample.
- Reference level 155.050 is broken by the 1H candle starting Jan 29 05:00 UTC,
  close 155.015; confirmation occurs 06:00 UTC (02:00 Halifax).
- Candidate left-hand liquidity high 155.5225 is at Jan 29 11:30 UTC (07:30 Halifax).
- During the 15:30–15:45 Halifax candidate liquidation candle, that reference
  liquidity is swept in the 15:35 minute and the candidate supply first retested
  in the 15:36 minute. Signal candle high/low: 155.612 / 155.209.
- Candidate entry remains ineligible until the signal closes at 15:45 Halifax.
  Previously checked synthetic-quote trigger occurs in the 15:51 minute.
- These source levels and originating candle are manually selected hypotheses
  requiring user confirmation, NOT automatic structure/POI identification.
  A nearby 1H candle at 02:00 UTC has similar bounds; do not claim source-image
  candle identity is unique despite feed differences.
- Chart and values saved as january29_candidate_mapping.png/.json. Context plot
  excludes incomplete/post-entry 1H candles; POI eligibility shading begins only
  after the reference break-confirmation time. No backtest rules are inferred
  solely from future trade outcome.

## Smallest fractal CHoCH confirmation

- User selected the LAST PULLBACK high/low as the fractal reference, not the
  immediately previous candle's extreme.
- A wick through the pullback reference is enough for a valid fractal break.
- A candle close beyond it improves confirmation/probability; it is NOT mandatory
  for fractal validity and does NOT by itself impose a HIGH-probability grade.
- Internal and swing breaks retain the mandatory candle-close rule. This
  supersedes any earlier generalization that every structure scale needs a close.
- Implemented distinction in structure_evidence.py for already identified,
  time-stamped references. It does not invent a pullback/pivot selection algorithm.
- Still to define: when a fractal pullback is considered complete and its extreme
  becomes the reference, before the later CHoCH. No fixed candle-count fractal
  or arbitrary lookback has been substituted.

## Fractal pullback construction — user's candle-sequence diagram

- User corrected the price-only retracement example: fractal pullbacks are based
  on candle/structure sequencing, not a fixed price distance or a requirement to
  return above the larger prior swing high.
- Diagram text: "When candle fail to break previous candle high and next candle
  after break the previous candle high. It will consider fractal low. It is
  mirror case for bearish market."
- Label the bullish sequence A, B, C: B fails to take A's high; a following C
  breaks the relevant preceding candle high, confirming a fractal low. The
  illustrated dashed low is under B. Do not automatically require an inside bar
  (both high and low contained) merely because the illustration resembles one.
- Exact breakout reference still needs confirmation: is C required to break
  B's high, or A's high? The pictured C breaks both, so the image alone cannot
  disambiguate that condition.
- Mirror bearish construction: failure to take the prior low, followed by the
  appropriate low break, establishes a fractal high. Wick break qualifies;
  closing confirmation adds quality per the user's earlier answer.
- Left diagram distinguishes minor fractal changes inside an internal leg from
  a later break of the larger internal reference. A fractal change alone does
  not automatically reverse internal or swing trend.
- Multiple failure candles, ties, outside candles and the exact extreme retained
  if several candles participate remain edge cases to validate; no arbitrary
  3/5-bar fractal rule or fixed swing-price retracement has been imposed.

## Fractal A/B/C breakout reference confirmed

- User explicitly confirmed: bullish C must break A's HIGH, not merely B's high.
- Bullish illustrated sequence: A establishes the comparison high; B fails to
  exceed A's high; C exceeds A's high. The illustrated pullback low is under B.
- Bearish mirror uses C below A's LOW after B fails to break A's low.
- Wick crossing remains sufficient; a close beyond A's level adds confirmation.
- Do not implement a rolling previous-candle break as a substitute for A's level.
- Repeated failure candles between A and the eventual breakout have not yet
  been specified: whether A stays fixed, and which candle extreme is retained
  across a multi-candle pullback, still needs confirmation before extending the
  illustrated A/B/C pattern into a general detector.

## Multi-candle fractal pullbacks confirmed

- User explicitly confirmed keeping the ORIGINAL A level fixed through multiple
  failed candles until a later candle breaks it.
- Bullish confirmation: price exceeds A's high; retain the LOWEST LOW of the
  intervening failed/pullback candles as the fractal-low reference.
- Bearish mirror: price trades below A's low; retain the HIGHEST HIGH of the
  intervening pullback candles as the fractal-high reference.
- This supersedes the earlier open question about multiple failures and rolling A.
- Confirmation candle C is excluded from the "intervening" extreme in the
  confirmed interpretation. If C also crosses that proposed extreme, ordering
  and reference validity require review; do not silently choose a favorable path.
- Candidate enumerator applies the literal rule to possible A candles and keeps
  nested/overlapping candidates with provenance. Selecting which candidate is
  fractal/internal/swing in the user's current narrative is a separate step.

## Internal pullback lifecycle — user-supplied annotated diagram

- User's image explains: an opposing fractal CHoCH starts an INTERNAL pullback.
  When fractal structure changes back into the internal trend direction, the
  pullback is more likely ending and internal continuation/BOS may follow.
- Bullish illustration: bearish fractal CHoCH begins the internal pullback;
  bullish fractal CHoCH restores alignment; a later break of the prior internal
  high is drawn as bullish i-BOS. The internal direction need not reverse merely
  because fractal direction changed against it.
- Mirror these relationships for a bearish internal trend.
- The user also assesses whether retracement is sufficiently meaningful to
  regard it as an internal pullback. Text says Fibonacci 0.36 to 0.5 is a "good
  pullback." Preserve exact 36–50% wording; do not silently change 0.36 to 0.382.
- Treat this as a qualitative depth preference for now, NOT an approved minimum
  36% filter, a maximum 50% eligibility cap, or an optimized threshold.
- Proposed causal interpretation needing confirmation: mark the pullback's
  extreme as a candidate internal higher-low/lower-high when fractal alignment
  returns, and confirm that internal pivot only when a candle CLOSES beyond the
  prior internal high/low. Do not assume a future internal BOS just from the
  alignment signal.
- Exact retracement endpoints and whether a minimum depth is required remain
  unconfirmed; do not backdate internal confirmation or reject deeper/shallower
  pullbacks based on the illustrative guideline alone.

## Internal pivot confirmation timing confirmed

- User confirmed the pullback extreme remains a CANDIDATE after fractal alignment
  returns, and becomes a confirmed internal higher-low/lower-high only after a
  candle CLOSE beyond the prior internal high/low (internal BOS).
- Do not backdate internal confirmation to the pullback extreme or to the earlier
  fractal realignment. An internal reversal also still requires a close through
  the existing protected internal boundary; a fractal reversal alone is not enough.
- Conditional internal pullback tracker implemented using explicit initial
  internal boundaries and timestamped fractal-direction evidence. It does not
  select the controlling fractal sequence or initialize the full hierarchy.

## Newer confirmed fractal level controls the next opposing CHoCH

- User confirmed the annotated example: internal direction is bullish, an older
  confirmed fractal low is 150.00, and a newer confirmed fractal low is 150.30.
  Price breaking 150.30 to reach 150.20 starts the internal pullback, although
  150.00 remains intact and no new internal bullish BOS has occurred.
- Use the newer confirmed low on the active fractal sequence for bearish CHoCH;
  wick crossing is sufficient under the existing fractal-break rule. Mirror the
  relationship with a newer confirmed high during bearish internal structure.
- Starting an internal pullback does not reverse internal direction or replace
  its protected boundary. Internal reversal still requires a close through that
  boundary; internal continuation confirms a candidate pivot only at its BOS.
- This resolves which of the two already confirmed fractal points controls the
  illustrated break. Discovering the active sequence from the nested diagnostic
  candidate pool and initializing the hierarchy remain separate work.

## Sequential A reset after fractal confirmation confirmed

- User confirmed the annotated A/B/C/D/E/F diagram. C breaks A's high and
  confirms B's fractal low; C then starts the next sequence as the new A.
- Before the next failed candle, each new higher-high candle advances A. In the
  diagram D makes a higher high than C, so D becomes the next comparison candle.
- E fails to break D's high, freezing D as A. F breaks D's high and confirms E's
  fractal low. Keep D fixed through multiple failures, retaining their lowest low.
- Apply the bearish mirror: advance A with new lower lows before failure; then
  hold its low fixed until broken, retaining the highest intervening high.
- This replaces the diagnostic all-possible-As approach for tracking a single
  directional sequence. The diagnostic enumerator is retained for comparison.
- Implemented FractalSequenceDetector for a supplied direction and first candle.
  It does not yet switch direction/reseed automatically at fractal CHoCH or
  initialize the internal/swing hierarchy. Same-candle outside-break ambiguity
  remains flagged; it is not silently accepted as a confirmed reference.

## Outside-candle order and context-versus-LC-1 timeframe correction

- User clarified the newly forming bullish A/B/C outside case: if C first
  breaks A's high and later B's low, this is fractal CHoCH. If it first crosses
  B's low and then A's high, there is no fractal break from that proposed point.
- The order must be observed; do not infer it from the final source-candle OHLC
  or treat high/low crossings within the same unresolved minute as ordered.
- This rule concerns the proposed newly forming fractal point. Do not use it
  to suppress an independent break of an already-confirmed protected reference.
- Most importantly: the user's CONTEXT fractal structure is checked on 4H/1H.
  The user uses fractal CHoCH differently for LC-1 on M15. Do not transfer the
  4H/1H A/B/C/context-fractal algorithm into M15 LC-1 qualification.
- The preceding M15 structure-map examples/reports were an assistant scope
  error; they do not validate either the user's context map or the distinct
  M15 LC-1 fractal-CHoCH rule. Original reports are retained with superseded
  applicability labels. Prior manually supplied LC-1 reference replays remain
  conditional execution examples, not automatic LC-1 structure qualification.
- Implemented a 60/240-minute context-mapper guard and complete-minute evidence
  checks for the newly forming outside point. Source-bar state is still made
  available at source close; lower-timeframe crossing minutes are evidence of
  order, not a claim that the full intrabar context engine is implemented.
- Exact M15 LC-1 fractal-CHoCH purpose/qualification is pending the user's
  separate explanation. No context rule has been substituted for it.

## M15 LC-1 role clarified: inducement near or inside the POI

- User explained that LC-1 requires inducement near the POI or inside it. The
  marked point may look like a M15 fractal high/low, but the user treats it as
  INDUCEMENT, not as the context-fractal trend map used on 4H/1H.
- Treat the selected M15 high/low as a liquidity reference for the LC-1 sweep.
  Do not add a M15 context-direction/CHoCH filter to entry eligibility.
- This resolves its role. It does not establish that every M15 pivot qualifies,
  a numerical definition of 'near', or an automatic method to select/grade its
  strength. Existing annotated liquidity inputs remain conditional references.
- The earlier entry rules remain: valid mitigated POI, qualifying LC-1 sweep,
  entry eligibility after the required M15 candle closes, and the confirmed
  entry/stop/risk rules. Context-fractal rules are not substituted for these.

## M15 inducement qualification: opposite-level break mandatory; wick sufficient

- User confirmed the sell-side sequence: the selected high must lead to a break
  of a previous M15 low before the high qualifies as inducement. Mirror buys:
  the selected low must lead to a break of a previous M15 high.
- User separately confirmed that a WICK through the prior level qualifies; a
  close adds confirmation/quality. Do not add a close-only eligibility filter
  to this liquidity qualification. The eventual LC entry candle still closes
  before the stop-entry order becomes eligible under the earlier entry rule.
- Implemented qualify_inducement in swing_lc1.py for explicitly selected M15
  origin and prior reference candles, separate from the 1H/4H context mapper.
  The prior level must have been available before the origin. The point is not
  available as inducement before its qualifying break. Completed-M15 evidence
  is published at source close; exact intrabar qualification is not modeled.
- Origin/prior selection, the definition of 'near', and the no-PBID-to-the-right
  rule remain to be validated. The helper does not certify every M15 pivot.
  A revisit of the origin before/with qualification is flagged for review.
- January 23 selected high 156.3585 qualifies against M15 low 156.252 on the
  13:30 UTC candle, available 13:45 with a confirming close. January 29 high
  155.5225 qualifies against the 09:00 UTC M15 low 155.0905 on the 15:15 candle,
  available 15:30 with a wick. This replaces the earlier close-only 15:45 timing.
  The prior H1 09:00 low happened to equal this M15 low; provenance is now M15.
- Both conditional reference reconciliations still produce the reviewed entry
  sequences. They remain selected examples, not automatic trade discovery or
  a profitability backtest. Eight new checks bring the relevant suite to 72 tests.
- A prior level already crossed before the selected origin, or a break inside
  the origin itself, is flagged for review rather than certified as a new later
  break. Intrabar origin ordering still needs separate evidence/definition.

## LC-1 inducement belongs to the left-hand leg

- User clarified with the LC-1 LID-sweep diagram: inducement is IN THE LEFT LEG.
- Bullish case: any qualifying HIGHER LOW formed in that left bullish leg may
  serve as inducement. On the later return, price takes that low and mitigates
  the valid demand POI; entry then follows the existing LC candle/order rules.
- Bearish mirror: use a qualifying LOWER HIGH in the left bearish leg, later
  taken as price returns into the valid supply POI.
- Keep the previously confirmed break qualification: the selected higher low
  must have led to a prior-high break (buy); the selected lower high to a
  prior-low break (sell). A wick qualifies, while a close adds confirmation.
  This new location clarification does not explicitly remove that requirement.
- 'Any' permits multiple qualifying points within the identified left leg.
  Do not silently restrict selection to one global extreme or the newest pivot.
- The left-leg location/HL-versus-LH role is now defined. Automatic identification
  of leg boundaries, specific pivot/reference pairing and any separate no-PBID
  admission rule remain to be validated. Existing selected-reference checks do
  not yet prove left-leg membership or automatically discover all inducement.

## Annotated candle example: user confirms BUY direction

- User confirmed that the latest TradingView candle sketch depicts a BUY.
  The red-above/blue-below position-box appearance does not determine the side
  of this example; use the user's explicit direction clarification.
- Read its right-hand sequence as: a higher low forms in the left bullish leg;
  the move from it takes the prior high, qualifying the low as inducement;
  the later downward candle sweeps that low and reaches the grey demand POI.
- Apply the established buy execution rules after valid LC candle closure:
  buy-stop at the LC high and protective stop at its low, without buffers.
  The demand POI and setup must remain valid. No extra M15 context-trend
  reversal filter is introduced by the low sweep.
- The screenshot is an explanatory sketch, not a new historical trade record
  or a measured price-path/entry-fill validation. Automatic leg/pivot selection
  remains unfinished; this confirmation resolves the intended side/sequence.

## Latest inducement rule: no formation-type, left-leg-only or no-PBID restriction

- User explicitly rejected the proposed 'no PBID to the right' admission filter:
  they do not care what forms, provided qualifying inducement is near or inside
  the POI and the trade meets the established rules when the POI is mitigated.
- A newer pullback inducement does NOT disqualify LC-1. Formation in the left
  leg is an allowed example, not an exclusive location requirement. This
  supersedes the earlier left-leg-only interpretation and pending PBID question.
- Retain the previously confirmed inducement break qualification (wick valid,
  close stronger), subsequent sweep, valid POI mitigation, LC candle closure,
  entry/stop placement and risk rules. This is not entry on a POI touch alone.
- Retain multiple qualifying inducement candidates; do not invent a rule to
  keep only the oldest, newest, strongest or most extreme point.
- The qualifier/scanner did not implement a PBID or left-leg-only gate, so no
  runtime filter was removed. Documentation and report scope now make the
  permissive formation rule explicit. Origin/prior selection and proximity
  interpretation still require automatic implementation/validation.

## Implementation progress: automatic M15 candidate enumeration

- Implemented a dedicated inducement candidate enumerator without importing
  the 1H/4H context-fractal mapper. This is implementation progress, not new
  user confirmation of pivot/proximity interpretation.
- Both marked January M15 origins appear after scanning all supplied candles
  without feeding their desired prices/times to detection. Eight new tests
  pass (80 combined relevant tests), as do 33 generated-pair comparisons with
  the existing independent selected-reference qualifier.
- Outputs retain multiple origin/prior alternatives. They are raw candidates,
  not automatic trades or proof of final LC-1 eligibility. POI proximity remains
  unresolved; the user has been asked how they distinguish near from too far.
- No arbitrary distance, pivot count, PBID restriction or optimization against
  recorded outcomes was added. Details and artifact paths: INDUCEMENT_DISCOVERY.md.

## Proximity resolved as quality only; inducement uses the entry timeframe only

- User clarified why 'near POI' was mentioned: it improves probability/quality,
  not admission. Any qualifying inducement in the left leg can be considered
  for entry; do not reject it because it is farther from the POI.
- Inducement is identified ONLY on the ENTRY timeframe (M15 in this plan).
  HTF structure references must not be substituted as LC-1 inducement.
- This removes the pending maximum-distance question and supersedes any earlier
  wording that required near/inside location for eligibility. The prior explicit
  no-PBID/no-formation-type exclusion remains; 'left leg' is not reinterpreted
  as a new exclusive gate in this clarification.
- Preserve the break qualification, sweep, valid POI mitigation, entry candle
  close, entry/stop/risk rules and concurrent/re-entry conditions. Proximity does
  not automatically assign HIGH probability or change position risk.
- LiquidityReference now has source_timeframe_minutes=15 and rejects 1H/4H
  context inputs. Signal metadata reports distance to the POI in USDJPY pips,
  with proximity_is_entry_filter=false. Candidate discovery metadata declares
  the M15 source timeframe and the same quality-only proximity policy.
- Three new checks pass (83 total relevant tests); both selected January
  execution reconciliations still pass. No distance threshold was optimized or
  inferred from their outcomes. Candidate lifecycle and full context/POI/entry
  integration remain separate implementation work.

## Implementation progress: automatic inducement-to-LC-1 connection

- Added scan_lc1_candidates and check_lc1_discovery.py. These use the complete
  automatically generated M15 candidate bank with annotated H1 zones/context;
  desired liquidity origins/prices and expected signal times are not detector
  inputs. No new user rule or backtest profitability is inferred by this stage.
- Both expected January initial signals and pending fills match. Jan 23 retains
  its one amendment; Jan 29 has none. Identical candle signals/support pairs
  are merged; pre-window consumed points and unresolved sequences are handled
  explicitly. No distance or PBID cutoff was introduced.
- Fixed stale mitigation handling: an old POI touch does not by itself authorize
  entry from a later liquidation candle wholly outside the POI. That unresolved
  case is now flagged for review, not automatically emitted as an entry.
- Jan 23's zone yields six raw signals over the later sample, Jan 29 one. The
  extra Jan 23 candidates need context, re-entry and position-lifecycle review.
  Do not call them confirmed trades, or selected-case matching a full backtest.
- Seven new tests pass (90 targeted total). Details and reproduction command:
  LC1_DISCOVERY_CONNECTION.md. Code changes after commit 4d5484e are currently
  uncommitted; that earlier Git bundle does not include this stage by itself.

## POI selection clarified by two user-supplied sketches

- User supplied two inline annotated sketches to explain origin selection.
  The second explicitly says POIs are drawn from the LEFT leg, more than two
  can exist in a leg, and a more extreme location improves probability.
- The extreme of the leg that produced an internal structure break is a POI
  source. Another POI can form in the middle of that leg with an inducement
  sweep, marked 'x'. The first image calls a POI with that sweep a good zone.
- Interpret the shaded areas as structural origin areas, not arbitrary candles
  preceding the break. Combine with the already confirmed single full-range
  candle boundary, confirmed structure break and initially unmitigated rules.
- Retain both extreme and qualifying mid-leg zones; do not impose one-POI or
  two-POI limits, a last-opposite-color rule, or an extreme-only admission gate.
- The sketches highlight sweep-backed mid-leg origins. They do not explicitly
  ban every possible mid-leg zone lacking a sweep; preserve other approved POI
  confluences rather than inventing such a universal exclusion.
- More extreme/sweep-backed improves contextual quality, not an automatic HIGH
  grade or numeric score. This is HTF POI origin analysis; it does not move the
  user's LC-1 inducement scan from the M15 entry timeframe onto 1H/4H.
- The first image's final sentence is cut off ('And if there is POI'); no rule
  is inferred from that missing continuation. These inline image descriptions
  are preserved in the notes; the image binaries are not workspace attachments.
- This clarifies selection patterns, not a completed automatic POI detector.
  Details: POI_SELECTION_FROM_IMAGES.md.

## Implementation progress: conditional HTF POI origin discovery

- Added poi_mapping.py with 1H/4H guards, close-based internal/swing break
  confirmation, full-candle source ranges and multiple origin candidates.
  Initial structure references/windows remain supplied. This is implementation
  progress, not new confirmation of ambiguous origin/freshness conventions.
- Both reviewed H1 zone origins/ranges appear without their desired times or
  prices supplied to the detector. Their internal reference levels/windows
  remain annotated. No automatic 4H aggregation anchor has been inferred.
- Ten new tests pass; full suite 146 tests. Evidence is kept separate from
  probability grades and active-zone admission. Nothing is sent to a broker.
- The Jan 29 next candle, 02:00 UTC (Jan 28 22:00 Halifax), has a full range
  155.5925–155.7840 inside the marked 01:00 UTC origin 155.592–155.790. It also
  produces a local break-supported candidate, with no proven sweep confluence
  in this scan. It is not automatically promoted as a second tradable zone.
- Prepared poi_origin_A_B_review.png to ask whether B should be a separate POI.
  Detailed limitations, freshness convention and audit: POI_MAPPING_STAGE.md.

## A/B origin review resolved: use A

- User explicitly selected A as the POI used in the reviewed Jan 29 example.
  A is 01:00 UTC (Jan 28 21:00 Halifax), range 155.592–155.790. The next
  contained candle B at 02:00 UTC is not an additional POI in this example.
- Implemented a narrow same-origin distinction: immediately following contained
  local-break candidate without independent sweep evidence is excluded beside
  a leg-extreme origin for the same confirmed structure break. The broader
  interpretation of other overlapping origin patterns is still to be validated;
  do not turn this one answer into a universal ban on nested or mid-leg POIs.
- Both marked January origins remain selected. Actual scan now retains one
  candidate for each reviewed zone, with B preserved in excluded_candidates
  and linked to retained origin A. No desired origin timestamps are used in
  the detector. Two new checks pass, including a mirrored demand case;
  148 tests pass across the full Python suite.
