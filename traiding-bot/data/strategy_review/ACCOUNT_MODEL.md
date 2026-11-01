# USDJPY account model — implementation assumptions and validation

`fx_account.py` is a pure ledger, not a signal detector or broker client.
It models USD 10,000 starting balance, 50:1 fixed gross initial margin and 1% of
available funds as the new-order stop-risk budget. User confirmed these settings.

## Explicit provisional conventions

- Equity = realized balance plus open P&L marked at the liquidation quote.
- Available funds = equity minus initial margin reserved separately per open
  trade. Opposing trades are not broker-netted; this is a gross-margin assumption.
- USDJPY units are USD base units. Fixed initial margin = units / 50.
- JPY trading P&L converts to USD at the exit/mark quote; no separate conversion fee.
- Risk budget is calculated at pending-order planning/replacement, not silently
  resized after a gap fill. Stop-risk estimate includes adverse entry/stop slippage
  and both commissions. Margin capacity includes entry fee and estimated initial
  spread/slippage loss.
- Whole USD base-unit increments are used for simulation, NOT verified IBKR
  minimum or lot-increment rules.
- Once another position uses margin, subsequent independent valid plans use the
  remaining available funds. No single-position restriction or daily-loss/news
  filter is introduced by the ledger.
- Entry and exit commissions are each charged once. Closing a trade releases its
  margin. A filled trade keeps its original stop and 2R target.
- Pending plans are checked for margin capacity again at fill. They cannot bypass
  newly committed margin; no automatic increase in leverage or silent resizing.
- Slippage/gaps can make risk at fill exceed the planning budget; report it.
- Equity can fall and available funds can become negative while holding a trade.
  The ledger does not silently simulate IBKR maintenance-margin liquidation.
  A portfolio backtest must report such events or implement an agreed stop-out
  policy before claiming broker-realistic leveraged performance.
- Financing/swaps, taxes and broker netting are absent. This is not verified
  IBKR account policy. The user accepted provisional transaction costs, not
  every implementation convention; preserve these distinctions in reports.

## Validation completed

Nine automated tests cover USDJPY-to-USD P&L conversion, fee-inclusive risk sizing,
concurrent available-funds sizing, leverage capacity, margin release, open P&L,
duplicate trade IDs, gap risk and rejection of stale plans with insufficient margin.

The two manually selected price-path reference cases were replayed through this
ledger using the previously assumed 1-pip spread / 0.1-pip slippage fills:

- January 23: USD 100 risk budget, 171,392 units, USD 3,427.84 initial margin.
- January 29: risk budget is recalculated from funds left after the first loss;
  see reference_accounting.json for quantities, margins and exact arithmetic.

These two examples are sequential. Concurrent-trade behaviour was checked using
synthetic unit tests, not a fully detected historical portfolio. No strategy
profitability, full sample validation or actual order execution is claimed.
