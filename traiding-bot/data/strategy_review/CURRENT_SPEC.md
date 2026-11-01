# USDJPY swing strategy — consolidated specification

Status: organized user rules, not yet fully machine-defined. Initial test version.
No automated USDJPY backtest has run. Source review documents and original files
are retained separately. Keep this private material out of GitHub.

## Account and test settings

| Setting | Current choice |
|---|---|
| Pair | USDJPY, long and short |
| Starting capital | USD 10,000 |
| Leverage assumption | 50:1 |
| New trade risk budget | 1% of available funds after existing margin usage |
| Concurrent trades | Permitted for independently valid setups |
| Re-entry | Permitted at a still-valid POI after a fresh setup |
| Target | Fixed 2R |
| Entry/stop buffer | None |
| Trailing exit / partial exits | Neither |
| Session filter | Off |
| Two-loss daily limit | Off for this initial test |
| High-impact news filter | Off for this initial test |
| Timestamp convention | America/Halifax, including daylight saving |

Provisional costs: total bid/ask spread 1 pip; additional adverse slippage 0.1 pip
on stop/market fills; commission max(USD 2, USD notional x 0.00002) per fill.
Also test total spreads 0.5 and 2 pips. USDJPY pip = 0.01 JPY. These estimates
are not verified broker charges. Initial results exclude overnight financing
and must be labelled accordingly. Exact available-funds/open-P&L and netting
conventions must be documented before margin-sensitive simulation.

## Structure and context

- Daily: broader narrative, not mandatory directional alignment.
- 4H/1H: narrative, immediate bias and POI selection; more weight on 4H.
- 15-minute: entry execution.
- Context structure has three scales: fractal (immediate), internal, swing.
  The context fractal algorithm below is used on 4H/1H. On M15 the user treats
  the qualifying high/low near or inside a POI as LC-1 inducement/liquidity.
  Do not use M15 context-fractal output as an additional LC-1 trend filter.
- User's latest fractal construction is a failure-then-break candle sequence:
  bullish case fails to take a previous high, then a following candle breaks the
  original A candle's high; bearish case mirrors it through A's low. Breaking
  only the intervening B candle's high/low is insufficient. Wick crossing can
  qualify, with close confirmation adding quality. Keep A fixed through multiple
  failed candles and retain their lowest low (bullish) / highest high (bearish).
  No fixed-price retracement rule.
- Sequential reset: C becomes the next A after confirmation. Before a failure,
  advance A with each new higher high (bullish) / lower low (bearish). After the
  first failure, freeze A until its level breaks; do not promote nested B breaks.
  This is implemented for a supplied direction and starting candle. The earlier
  nested-candidate enumerator remains a separate diagnostic comparison tool.
- Outside A/B/C order, bullish case: A-high first, then the proposed B-low
  crossing means fractal CHoCH. B-low first, then A-high means no fractal break
  from that newly forming point. Use observed lower-timeframe ordering; missing
  data or both first crossings in the same minute remains unresolved. Keep
  breaks of previously confirmed protected levels separate from this case.
- An opposing fractal CHoCH starts an internal pullback. Fractal alignment
  returning suggests continuation but leaves the pullback extreme a candidate.
  Confirm the internal pullback pivot only when a candle CLOSES beyond the prior
  internal high/low (internal BOS). Mirror this sequence for bearish structure.
- A newer confirmed low on the active fractal sequence becomes the reference
  for bearish fractal CHoCH. Its wick break can start the internal pullback while
  an older fractal low holds, without waiting for a new internal BOS. Mirror with
  newer confirmed highs in bearish internal structure. The protected internal
  boundary remains separate and still requires a close for internal reversal.
- The illustrated 0.36–0.5 retracement is a soft quality preference, not a required
  minimum, a maximum-depth filter or a fixed-price pullback definition. Exact
  retracement endpoints still need validation against the user's annotations.
- Swing turning point is identified via internal reversal. Internal and swing
  breaks require candle closes; fractal wick breaks remain valid as above.
  Do not backdate confirmation to an old pivot or the earlier fractal realignment.
- Clear aligned trend: swing and internal point in the same direction.
- Qualifying 1H POIs can be used; nested 4H/1H POIs are preferred, not universally
  mandatory. Weak/unclear 4H with clear 1H can justify emphasis on 1H.
- Countertrend fractal CHoCH can still support a valid lower-quality setup.
  Quality and eligibility are separate; strong reversal contexts can improve
  quality. Do not apply a universal countertrend or phase-D ban.
- Apply the A/B/C/D and range guidance transcribed in PHASE_RULES.md, with
  mitigation/objective context. Do not invent numeric momentum thresholds.

## POI creation and lifecycle

1. A POI is one selected candle's full high-low, including wicks; colour irrelevant.
2. Mandatory: leads to a confirmed structure break and initially unmitigated.
3. Keep multiple qualifying candle POIs in a leg, including mid-leg zones.
   The user's two POI-selection sketches clarify where to look: draw from the
   LEFT leg that produced the confirmed break. Its origin extreme is a POI
   source; a middle-of-leg origin associated with an inducement sweep ('x')
   is another valid highlighted pattern. More than two POIs may qualify.
   A more extreme location improves quality; it is not an extreme-only filter.
   Select the actual origin candle's full range, not every candle before BOS.
4. Use the plan's sweep/flip/stacking/pricing/liquidity/chain confluences for
   contextual quality. Not every confluence is mandatory; no score cutoff confirmed.
5. First 15-minute wick/body touch is mitigation. A touched zone is not necessarily
   invalid: keep its state distinct from a newly selected fresh zone.
6. Any price breach through its far edge invalidates it immediately: demand below
   its low, supply above its high. No closing confirmation or extra buffer.
7. Remove failed zones from setup eligibility and cancel their unfilled entries.

Selection details transcribed from the user's images are in
POI_SELECTION_FROM_IMAGES.md. The sweep shown there supports HTF POI quality;
it is separate from the entry-timeframe-only LC-1 inducement scan. The sketches
do not change the mandatory confirmed-break/freshness requirements or introduce
an automatic numeric probability score. Automatic structural origin discovery
still needs implementation and comparison with the existing marked zones.

## LC setup and order lifecycle

- LC-1: LID sweep; LC-2A: pullback fake break; LC-2B: equal-high/low sweep.
  Use source diagrams and journal examples; exact structure-level identification
  and equality tolerance are still to be made deterministic.
- Inducement is identified ONLY on the entry timeframe, currently M15. The
  selected level may look like a fractal high/low, but is liquidity for the sweep.
- Proximity to/inside the POI improves contextual quality, not eligibility. Any
  qualifying inducement may be used; there is no maximum-distance rejection.
  No numerical proximity score or automatic HIGH grade has been approved.
- Any qualifying inducement may be used, regardless of
  whether it formed in the left leg or during a pullback. A newer inducement to
  the right does not disqualify LC-1. Do not impose a no-PBID or left-leg-only
  filter. Keep multiple qualifying points; no extreme-only/most-recent-only
  restriction is confirmed. Entry still requires the established LC rules.
- Mandatory inducement qualification: a selected SELL high must lead to a break
  below a prior M15 low; a selected BUY low must lead to a break above a prior
  M15 high. A wick qualifies; a close adds quality. The level becomes usable
  only after qualification. Do not require context-trend alignment on M15.
- Candidate/prior-reference selection remains to be validated. Existing replays detect the qualifying break
  from annotated origin/prior inputs. Left-leg boundaries are not an LC-1
  admission requirement; context hierarchy mapping remains a separate task.
- Liquidity liquidation can precede or occur within the POI, but entry requires
  POI mitigation and a still-valid setup.
- Early invalidation for LC-1/LC-2A BEFORE POI mitigation: after inducement is taken,
  next-candle wick above liquidation-candle high invalidates a buy; next-candle
  wick below liquidation-candle low invalidates a sell. No close required.
- After a qualifying M15 candle closes: buy-stop at high with stop at low, or
  sell-stop at low with stop at high. No entry or stop buffers.
- Amend UNFILLED entries using subsequent qualifying closed candles: move both
  entry and protective stop to the new candle extremes; recalculate size from
  1% of available funds. Do not amend from incomplete future candles.
- Once filled: fixed initial protective stop and 2R target; no trailing or partials.
- Re-entry requires another fresh valid setup at a POI that has not failed.
- Use lower-timeframe sequencing for within-bar entry, mitigation, invalidation,
  and stop/target conflicts. Flag unresolved ordering rather than favor the trade.

## Evidence already organized

- 109 journal rows, no duplicate date/time/pair/setup keys in the initial audit.
- Recorded fixed-target outcomes: 66 wins, 43 losses, +89R before reconstructing
  real execution/costs. This is descriptive manual-journal evidence, not a new test.
- 321 linked images recovered, 307 distinct image hashes. All existing links have
  downloaded images; six nominal timeframe slots lacked links in the workbooks.
- Visual review so far covers 15 images from six representative records; no
  claim that all images have been visually reviewed or independently validated.
- Source plots are OANDA on FXReplay; substituting IBKR prices can change candles,
  trigger sequencing and results. Future price-data provenance must be explicit.

## Remaining implementation gaps — do not hide with assumptions

- Causal initialization of the fractal sequence, chart validation of provisional
  reversal linking, resolution of outside-candle sequences, initialization of
  internal/swing boundaries, and identification of which scale each candidate
  POI broke. The directional A reset rule and internal pivot confirmation timing
  are confirmed; direction-change linking is implemented provisionally.
- Consistent phase/range identification and discretionary POI ranking from the
  supplied chart references, without outcome-dependent labelling.
- Precise LC-1/2A/2B liquidity references and model-specific qualification.
- Whether early invalidation applies only to the immediately next candle;
  order expiry/validity and allowed direction of pending-entry amendments.
- Historical bid/ask data, financing exclusion, price-feed/timezone aggregation,
  margin/netting conventions and size increments.
- Journal date/time corrections are now confirmed and retained in date_corrections.json.

## Implementation status

- Corrected sample: 9,975 one-minute bars; all 665 overlapping M15 bars reproduce
  exactly. No claim of independent exchange-calendar or OANDA price equivalence.
- Two manually identified M15 signal references replayed for execution timing;
  no automatic POI/phase/LC eligibility detection or full backtest yet.
- Pure risk/account ledger implemented in fx_account.py and checked with nine
  unit tests plus those two sequential reference fills. Details and provisional
  margin/size conventions are in ACCOUNT_MODEL.md. No live connection or orders.

Next work: formalize and validate causal structure/POI/LC detection against the
provided chart annotations before claiming an automated strategy backtest.

LC-1 sequence stage now implemented conditionally in swing_lc1.py and exercised
with check_swing_reference.py. With annotated origin/structure/liquidity inputs,
it finds the Jan 29 closed-candle setup and the Jan 23 initial order plus one
entry/stop amendment. This does not remove human selection of those inputs.
See LC1_IMPLEMENTATION.md for exact annotated levels, review-required cases and
the 24 passing sequence/account/price-path tests.

Multi-candle fractal candidate stage is now implemented and checked with ten new
tests. Its full-data scan includes all four reviewed January reference extremes
without supplying those prices/times to detection. This is candidate enumeration,
not final structural hierarchy or signal selection. See FRACTAL_CANDIDATE_STAGE.md.

Conditional internal pullback tracking is implemented in internal_structure.py.
It keeps candidate extremes separate from confirmed internal pivots, requires
close-based internal continuation/reversal, and records confirmation availability
at candle close. Initial boundaries and controlling fractal-direction changes
remain explicit inputs; this stage does not automatically map the full hierarchy,
assign phases, or create orders. See INTERNAL_STRUCTURE_STAGE.md.

Sequential A selection within a supplied direction is now implemented as
FractalSequenceDetector in fractal_candidates.py. Ten additional checks cover
the confirmed A/B/C/D/E/F example, bearish mirror, repeated cycles, frozen A,
wick confirmation, equal levels, ordering ambiguity and causal availability.
All 36 sequence/candidate/internal/break-evidence tests pass. Fixed-direction
full-sample scans are saved in fractal_sequence_audit.json; they are not an
automatic changing-trend map or strategy backtest.

Provisional fractal CHoCH linking is implemented in fractal_structure.py for
1H/4H only; M15 context mapping is rejected. The prior mixed H1/M15 three-of-four
comparison is superseded by the user's timeframe correction. Those reports are
retained as history and are not valid context-map or LC-1 validation.

Complete minute data can resolve the newly forming outside-point order using
the confirmed high-first/low-first rule. Missing coverage, OHLC mismatch, both
first crossings in one minute, or additional uncertain reversals remain flagged.
All 54 structure tests plus 18 LC-1 qualification/sequence tests pass. Initial context direction,
other reversal-linking conventions, swing initialization and automatic M15 LC-1
inducement selection remain unfinished. Its role as liquidity near/inside the POI
is now confirmed. No full automated USDJPY backtest has run.
See FRACTAL_CHOCH_STAGE.md and context_structure_audit.json for current scope.

M15 inducement break qualification is now implemented in swing_lc1.py and used
by check_swing_reference.py. Eight checks cover the mandatory break, wick timing,
close quality, mirrored BUY case, future reference rejection and uncertain origin
revisit, already-crossed prior levels and breaks inside the origin candle. The
January references use M15 prior levels, and both selected trade
sequences reconcile. Exact origin/prior selection remains annotated.

Automatic break-supported M15 candidate discovery is implemented in
inducement_candidates.py. Eight new tests bring the relevant suite to 80 passing
tests. The full 6,043-bar scan independently includes both marked January M15
inducement origins. Multiple origin/prior pairings are retained; identifying a
candidate is not validation of proximity, pivot interpretation, phase or entry.
Thirty-three actual generated pairs also match the selected-reference checker.
Proximity is now clarified as quality-only, not an admission filter. See INDUCEMENT_DISCOVERY.md
and inducement_candidate_audit.json; no full automated backtest has run.

LC-1 liquidity references now explicitly declare the M15 entry timeframe and
reject context-timeframe inputs. Signals report inducement-to-POI distance in
pips as descriptive information, with proximity_is_entry_filter=false. Three
additional checks cover distant inducement, inside-POI reporting and timeframe
separation (83 total relevant tests). Both conditional January replays pass.

Automatic inducement-to-LC-1 connection is implemented as scan_lc1_candidates
and exercised by check_lc1_discovery.py. Supplied inputs remain the H1 POI
origin/confirming level and approved context; marked M15 inducement levels and
expected signal times are not detector inputs. Duplicate origin/prior supports
and identical signal candles are merged. Pre-window consumed points are excluded
under the provisional freshness interpretation. An old POI touch does not
automatically authorize a later liquidation candle wholly outside the POI;
that case is review-required.

Both expected initial signals and pending-order fills match the January
references. The Jan 23 zone generates six candidate signals over the remaining
sample; Jan 29 generates one. The extra Jan 23 candidates require changing
context, reference choice, re-entry and position-lifecycle validation. These
are not six confirmed trades or a profitability backtest. Seven new tests pass,
bringing the targeted suite to 90. Details: LC1_DISCOVERY_CONNECTION.md and
lc1_automatic_inducement_connection.json.

HTF POI candidate origin discovery is implemented in poi_mapping.py for supplied
internal/swing reference levels and mapping windows. It discovers the origin
candles rather than accepting their desired timestamps. Both reviewed January
H1 origins/ranges and internal-break availability times are reproduced. Twelve
tests pass; the full suite passes 148 tests. This is conditional mapping, not
automatic structural hierarchy, probability grading or a full backtest.

Pre-confirmation freshness uses an explicit provisional M15 closed-departure
convention followed by wick-overlap return checks. It is an observed-path audit,
not a validated resolution of every intrabar formation/retest. Candidates carry
requires_mapping_validation=true and are not automatically sent to entries.
The user selected Jan 29 origin A (01:00 UTC, 155.592–155.790), not contained
next candle B (02:00 UTC, 155.5925–155.7840). B is now recorded as an excluded
same-origin candidate. The implemented pattern is narrow: an immediately
following contained local candidate without independent sweep evidence is not
another origin beside that leg-extreme candle. This is not a blanket ban on
nested 4H/1H zones or separately qualifying mid-leg sources. Details and
image: POI_MAPPING_STAGE.md, poi_origin_mapping_audit.json, poi_origin_A_B_review.png.
