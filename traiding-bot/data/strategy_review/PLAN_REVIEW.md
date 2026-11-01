# USDJPY swing strategy — organization draft

Status: source review only. Not an executable specification or a new backtest.
No strategy parameters have been optimized, orders placed, or original files edited.
This document is in the repository's ignored data directory; do not commit the
private plan or journals to GitHub without the user's explicit instruction.

## Sources and completeness

- Notion export: `Swing Trading Plan 2b4f66962cbc80b499add2804afbc51c.md`.
- Five exported images, all visually reviewed: `LC-1_Requirements.png`, `LC-1.png`,
  `LC-2A.png`, `Screenshot_2024-10-03_185409.png`, and
  `Screenshot_2024-06-06_132439.png`.
- Three uploaded workbooks: Swing USDJPY Round 1, Round 2, Round 3.
- Archive contains one Markdown page, not separate subpage documents.
- HIGH PROBABILITY EXAMPLES contains three generic app.notion.com links without
  exported example content. The external invalid-LC1 TradingView chart was not read.
- The screenshots include teaching material. Treat their rules as candidate
  explanations; ask which ones the user actually follows.

## Explicit rules in the user's written plan

### Market, risk and management

- Pair: USDJPY. Bullish and bearish entry models are shown; confirm both are traded.
- Risk: 1% per trade. Equity basis, sizing units, account currency, margin/leverage,
  spread, commissions and overnight financing remain unspecified.
- Stop taking entries after a maximum of two losses per day. Trading-day boundary,
  treatment of simultaneous positions, and whether losses must be consecutive need definition.
- Fixed target: 2R. No partial exits and no trailing exit stop.
- No entry less than 30 minutes before high-impact news. Relevant currencies,
  event calendar, exact boundary, resumption time and pending-order handling unspecified.
- Session text says "4 pm to - (Sydney), 7pm to - (Tokyo)". Timezone,
  daylight-saving handling and both ending times are missing.
- Do not import the former SPY strategy's 3.3R target, moving averages, $0.05
  buffer, cash-only size cap or crossover exits into this independent strategy.

### Context and point of interest

Written primary mapping: 1D/4H context -> 1H medium-timeframe POI -> 15M execution.
Mandatory POI properties: led to a structure break (CHoCH/i-BOS/BOS), and unmitigated.
Other listed confluences: liquidity sweep; flip; zone created in a swept session;
strong target liquidity/inducement; stacked higher-timeframe zone; premium/discount
pricing; corrective mitigation; chain of mitigations.

Context checklist records trend/order-flow direction, continuation/pullback,
fractal/internal/swing break, momentum shift, zone significance, pricing,
freshness, delivery type, completed objective, supply/demand control and liquidity.
These are not yet objective binary rules. In particular, clarify whether a
correctively mitigated zone is eligible despite the mandatory unmitigated rule.

### Execution sequence

1. Wait for mitigation of a selected MTF POI.
2. Identify qualifying liquidation: LC-1 LID sweep, LC-2A fake break, or LC-2B equal-high/low sweep.
3. Validate with the early-invalidation method.
4. After the liquidation candle closes, place a stop-entry order beyond that
   candle in the trade direction, with buffers.
5. Reposition the UNFILLED entry order beyond subsequent candles until filled
   or the POI fails. This pending-entry adjustment is distinct from trailing an
   open position's stop loss, which the plan disallows.
6. Once filled, manage to fixed 2R or stop. Stop placement and any other exits
   need confirmation; do not infer them from our earlier SPY discussion.

For automation, entry buffer, stop buffer, stop location, order replacement
direction, validity checks, expiry, zone failure, and re-entry limits must be defined.

### Entry models and illustrations

- LC-1: small/tight range, MTF LID, early invalidation; near/inside zone optional.
  Diagram: sweep a strong high/low associated with a structure break; no PBID
  to the right; POI mitigation must occur before entry eligibility.
  Requirements illustration emphasizes high/higher-medium-quality contexts,
  tight ranges, and starts of phases A/C; its "see it on one screen" test is
  subjective and cannot be directly encoded without an agreed proxy.
- LC-2A: small fake breakout, valid early invalidation. Near/inside the zone and
  not closing beyond the marked level are listed as optional. Diagram sweeps
  the extreme pullback high/low that caused the prior fractal break. Entry
  eligibility still requires POI mitigation.
- LC-2B: equal highs/lows formed just before the zone; early invalidation.
  No dedicated LC-2B diagram is included.
- CE/DCE illustration exists, but text does not say these are enabled setups.
  Do not add them without confirmation.

## Conflicting versions that must not be silently combined

- Main headings: 1H POI / 15M execution.
- Later MAPPING section: weekly/daily/4H context, M15 immediate bias, M5/M1 execution.
- Phase illustration has both swing and day columns: swing includes 1D context,
  4H/1H POIs and M15 execution; day includes 4H context, M15 POIs and M5/M1 execution.
- Journals include London/New York as well as Sydney/Tokyo entries, while written
  session restrictions list only Sydney/Tokyo with incomplete clock times.
- Written scoring differs from some journal grades. Confirm whether scoring is
  descriptive, a hard admission filter, or changed between rounds.

## Confluence score table transcribed from plan

| Criterion | Points |
|---|---:|
| Structure break | 2 |
| Flip | 2 |
| Zone created in swept session | 1 |
| Swept liquidity | 2 |
| Strong liquidity to target | 1 |
| Stacked HTF zone | 2 |
| Premium/discount/FVG pricing | 1 |
| Unmitigated | 1 |
| Corrective mitigation | 1 |
| Chain | 1 |

Total possible points: 14. HP 11–14, MP 7–10, LP 0–6 (avoid, per table).
Mandatory POI conditions still apply regardless of total score.

## Journal inventory and issues

| Workbook | Nonblank dated trade rows | Recorded fixed-R outcomes |
|---|---:|---|
| Round 1 | 57 | 31 at +2R, 26 at -1R |
| Round 2 | 15 | 12 at +2R, 3 at -1R |
| Round 3 | 37 | 23 at +2R, 14 at -1R |

109 rows before any duplicate review or exclusions. These are journal-derived
outcomes, NOT independently verified historical test results.

- Round 1 dates are in 2023. Round 2 is predominantly 2024 but includes
  2025-08-11. Confirm the year rather than correcting it automatically.
- Round 3 has a text date `01/06/25` in Trades!A18. Header is DD/MM/YY; confirm
  intended date before normalizing. Rows in rounds 2/3 are not fully chronological.
- Cached #REF! strings exist, including Round 1 summary/drawdown/streak outputs.
  Rebuild metrics from cleaned trade rows rather than trusting cached summaries.
- Fixed R outcomes use column O, while TOTAL R column AB references column N,
  MAX R. The latter is not cumulative realized equity. Existing drawdown
  formulas based on it should not be treated as strategy drawdown.
- Net Return uses total fixed R minus 0.3 times winning-trade count in the
  uploaded settings/formulas. Ask what that deduction represents; it is not a
  verified broker transaction-cost model.
- MAX R is calculated from MFE divided by entry-candle size plus configured
  buffer, with an MAE-buffer condition. MFE/MAE summaries alone do not establish
  whether target or stop was reached first; chronological intrabar data is needed.
- Columns identify date, entry time, session, pair, setup, confluences,
  probability, phase, news, candle size, MAE/MFE, outcomes and chart URLs.
  There are no explicit standardized direction, entry-price, stop-price,
  exit-price or exit-time columns. Some chart links are missing.
- Need to learn whether rounds are consecutive periods, different rule versions,
  or repeated reviews, and whether every eligible setup was recorded.

## Clarifications in a practical order

First: select the authoritative timeframe version, trading timezone/session
windows, 2R target, and setup models to enable. Ask whether journals are live,
paper, or manual historical replay and whether their rules changed by round.

Then define structure and zones: confirmed swing/fractal construction without
future-data access; close-vs-wick breaks; exact supply/demand zone boundaries;
zone creation/failure/mitigation; liquidity/LID/PBID and equal-level tolerances;
early invalidation. Use two or three actual annotated journal examples to
resolve definitions instead of substituting generic technical indicators.

Then define orders/risk: entry and stop buffers in pips; JPY pip size; stop anchor;
unfilled-order movement and cancellation; 1% sizing with USDJPY/account-currency
conversion and margin constraints; maximum simultaneous exposure; daily loss
reset; news eligibility; target/stop precedence and overnight/weekend handling.

Finally agree data feed, bid/ask or spread assumptions, fees/swaps, test dates
and a reserved validation period. Use a small journal reconciliation sample
to check signal identity and prices before running the full backtest.

No strategy backtest should start until the relevant definitions are confirmed.
