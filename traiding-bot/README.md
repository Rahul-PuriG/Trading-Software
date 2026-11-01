# IBKR paper trading — local Windows execution

## USDJPY swing-plan validation sample

The pure `fx_account.py` ledger models risk and margin separately from signal
detection. Test with `python -m unittest test_fx_account -v`. It assumes gross
initial margin, equity including marked open P&L, and whole USD base-unit sizing;
these are labelled simulation conventions, not broker-verified behaviour.
`reference_replay.py` checks two manually chosen price paths and does not detect
strategy signals or produce a full profitability backtest.

`swing_lc1.py` qualifies selected M15 inducement highs/lows only after they cause
an opposite prior-level break: a wick is sufficient, and a close adds quality.
It then checks the sweep/POI/closed-candle sequence conditional on annotated
zone, origin/prior-reference selection and context inputs. `check_swing_reference.py` reconciles two
examples and checks pending entry/stop amendments and risk replanning. It does
not automatically identify structure pivots, select POIs or grade phases, and
does not implement LC-2A/LC-2B. Do not report its selected examples as a full or
out-of-sample strategy test. No broker orders are sent by these modules.

Inducement is identified on the M15 entry timeframe only. Any qualifying point
may be used; proximity to/inside the POI improves quality, not eligibility. This includes one
formed in a pullback. A newer inducement does not disqualify LC-1; no left-leg-only
or no-PBID admission filter applies. Mandatory break/sweep/mitigation and entry
rules still apply; exact point selection remains annotated in the replays.
Signal metadata reports distance in pips without using it as a rejection filter.

`inducement_candidates.py` automatically enumerates M15 origins and prior-level
break evidence, retaining multiple candidates. It is separate from context
structure mapping. Its outputs still require POI/proximity and setup validation;
candidate counts are not trades, and no automated profitability test is implied.

`fractal_candidates.py` includes the diagnostic nested-candidate enumerator and
`FractalSequenceDetector`, which advances A before a failure, freezes it during
the pullback, and resets to the breakout candle C. The sequence detector requires
a supplied direction and starting candle; automatic CHoCH direction changes and
hierarchy initialization remain unfinished. `internal_structure.py` tracks
internal pullbacks from supplied boundaries and fractal-direction evidence. It
keeps a candidate pivot unconfirmed until a close beyond the prior internal
level; fractal realignment alone is insufficient.

`fractal_structure.py` maps context fractal CHoCH on **1H/4H only** and can feed
direction evidence to the internal tracker on the same timeframe. It rejects
M15 context mapping: the user's M15 LC-1 highs/lows serve as inducement near or
inside the POI, with exact liquidity selection still supplied as annotations.
They do not provide the 1H/4H context-fractal trend signal. For the bullish outside A/B/C case, high-first then
low produces CHoCH; low-first then high produces no break from that proposed
new point. Complete, matching one-minute evidence is required to choose the
order; same-minute or missing evidence remains unresolved. Initial direction
and reversal linking conventions still need chart validation. This is not a
validated full-history hierarchy or automated strategy backtest.

The user's USDJPY swing plan is separate from the earlier experimental SPY SMA
strategies below. Its rules and journals are organized privately under the ignored
`data/strategy_review/` directory. An automated USDJPY strategy backtest has not
yet been implemented or validated.

`download_usdjpy_sample.py` downloads a read-only IBKR historical sample to
reconcile the January 23 and January 29, 2025 journal examples against candles:

```powershell
.\.venv\Scripts\python.exe download_usdjpy_sample.py
```

Keep TWS paper trading running on port 7497. Uses client ID 19 and the existing
`ib_async` dependency and `bot.py` paper-account check. Read-Only API can stay on.
No order submission/cancellation is performed. Default downloads:

- 15-minute MIDPOINT context: November 1, 2024 through January 31, 2025.
- 1-minute MIDPOINT execution sample: January 22 through January 30, 2025.

Request dates use America/Halifax local midnight, with exclusive end dates. CSV
timestamps are UTC and identify the candle start. Successful nonempty chunks
are cached for retry; an empty request can indicate a weekend/holiday or missing
data and is reported in metadata. Coverage and timeframe alignment require later
inspection; a completed download does not prove a complete historical backtest.

Downloader version 2 requests one-minute bars in explicit four-hour windows.
The initial daily-request version returned partial FX sessions in the uploaded
sample. Version 2 validates minute timestamps against every downloaded 15-minute
bar in the execution range before accepting the execution CSV. It reuses the
existing 15-minute cache, but the revised one-minute requests use new cache keys.
If coverage fails, it writes `USDJPY_execution_1min_INCOMPLETE.csv`, marks
`metadata.json` as failed and exits with an error; do not use an old standard-name
execution file as if that run had succeeded. The check does not independently
prove all 15-minute context bars are present.

Outputs in `data/usdjpy_sample/`: `USDJPY_context_15min.csv`,
`USDJPY_execution_1min.csv`, and `metadata.json`. These contain prices and request
metadata, not account summary or credentials. Share those three files for review.
TWS historical-data permissions are required. OANDA/FXReplay journal prices may
differ from IBKR IDEALPRO midpoint prices. No bid/ask fills or 4H/daily bar
aggregation anchors have been inferred. If one series fails, previously saved
data/cache remains available; inspect the error before proceeding.

## Six-month SPY backtest

### Risk-sized strategy with stop and 3.3R target

`risk_backtest.py` imports the updated `backtest.py` and uses the same slow,
long-only signals. It buys at the next available 5-minute open after a completed
30-minute signal. The stop is the **signal candle low minus $0.05**, configurable
with `--buffer`. A sell closes the long; there are no short entries.

```powershell
.\.venv\Scripts\python.exe risk_backtest.py --start 2026-05-01 --end 2026-11-01 --risk-pct 1 --reward-r 3.3 --buffer 0.05
```

Whole-share position sizing budgets 1% of current flat account equity, including
modelled entry/stop slippage and round-trip commissions. Available cash caps
the position: this is **up to** 1% planned risk with no leverage. If even one
share cannot fit, the entry is skipped. Gaps through the stop can cause losses
larger than the budget. Target is entry plus 3.3 times the entry-to-stop price
distance; realized net R can be lower due to costs and crossover exits.

Exit at stop, target, or bearish crossover, whichever occurs first. Positions
can remain overnight. Checks use the original 5-minute OHLC data; when stop and
target are both touched in one candle the stop is assumed first. A stop gap
fills at the opening price less slippage. Target fills are at the limit, even
if the open is above it. Intrabar event timestamps identify the 5-minute candle,
not an exact execution second. No tick-level queue/liquidity model is available.
Final open positions are liquidated at the final close with modelled costs.

Reports are saved separately in `reports/risk1_rr3_3/`. They include exit reasons,
position quantities, stop/target levels, planned risk, realized net R, and a
cash-matched buy-and-hold comparison. Default costs remain $1 per order and 1 bp
slippage per side. Compare returns carefully: earlier tests used one share,
while this version sizes positions from risk. Neither script submits orders.

### Slower comparison strategy

The fixed `slow` strategy aggregates the existing bars into complete 30-minute
candles anchored at 09:30 New York time. It enters on an SMA10 upward crossover
of SMA30 only when that candle closes above SMA100, and exits on the downward
crossover. Entry is not delayed until the filter passes: a fresh crossover is
required. Signals use completed candles and fills use the next candle's open.
Positions and averages carry overnight; one share, long/flat, no stop loss.
The original strategy remains the default. This version is a hypothesis, not a
proven improvement; these six months have already influenced its design and
cannot serve as untouched validation data.

After replacing `backtest.py`, reuse the existing download:

```powershell
.\.venv\Scripts\python.exe backtest.py run --strategy slow --start 2026-05-01 --end 2026-11-01
```

Results go to `reports/sma_10_30_trend100/`, leaving the original reports in place.
The default $1/order commission and 0.01% slippage still apply. Drawdown uses
30-minute closing equity, so intrabar drawdown can be larger. At least 100
pre-period 30-minute candles are required; the downloaded extra weeks should
provide enough, but insufficient warmup fails rather than shortening the test.
No new packages, TWS connection, download, or orders are needed for `run`.

### Original strategy and data download

`backtest.py` tests the 5/20 SMA crossover on 5-minute SPY TRADES bars during
regular market hours. Buy one share after an upward crossover; exit after a
downward crossover. No shorting or additional entries while long. Signals use
completed candles, with fills modelled at the next available candle's open
(including next-session opens). Averages and positions carry across sessions.
The final open position is liquidated at the final close for reporting.

Run in this folder with TWS paper trading connected (Read-Only API may stay on):

```powershell
.\.venv\Scripts\python.exe backtest.py download --start 2026-05-01 --end 2026-11-01
.\.venv\Scripts\python.exe backtest.py run --start 2026-05-01 --end 2026-11-01
```

The end date is exclusive: these commands cover May 1 through October 31, 2026.
The download also requests earlier warmup bars. No orders are sent by either
command. Historical data requires appropriate IBKR permissions/subscriptions;
paper account access alone does not guarantee data entitlement. Downloading
takes multiple weekly requests. Successful weeks are cached locally and reused
if you rerun the command. Delete only a specific cached `week_*.json` file to
refresh that week. IBKR errors or empty weeks stop the download rather than
producing a shorter test. Use a separate `--data` directory for a different dataset.

The run validates 5-minute bar coverage against IBKR's exchange session schedule,
including holidays and early closes, before reporting performance. It writes:

- `reports/sma_5_20/summary.json`: net P&L, trade count, win rate, drawdown,
  profit factor and a one-share buy-and-hold comparison.
- `reports/sma_5_20/trades.csv`: entries, exits and net trade results.
- `reports/sma_5_20/equity.csv`: marked-to-market account equity by candle.

Defaults: $10,000 starting cash, one share, $1 commission per order and 1 basis
point (0.01%) slippage per side. Change costs with `--commission`,
`--slippage-bps`, and `--capital` on the `run` command. The costs are modelling
assumptions, not a statement of your actual IBKR fees. This is a cash account
simulation with no leverage, dividends, taxes, interest or partial fills.
Historical adjustments follow IBKR's TRADES data. Profit factor is null when
there are no losing trades; win rate is null when there are no trades.
Dollar P&L and one-share benchmark help interpret the account return because
most of the $10,000 remains uninvested. No parameter optimization is performed.

Data and reports are ignored by Git. Actual six-month performance has not been
verified until real data is downloaded and the `run` command succeeds.
Synthetic unit tests validate execution timing and accounting, not profitability.

This first version connects to TWS on your Windows computer. It reads account
information and open orders, previews stock limit orders, and can explicitly
submit or cancel paper orders. Strategies are not included.

## 1. Configure TWS

Log in to **Paper Trading**, then open **File → Global Configuration → API → Settings**.

- Enable **ActiveX and Socket Clients**.
- Confirm the socket port is **7497** (the default paper TWS port).
- Keep **Read-Only API** checked for the initial account check.
- Keep connections limited to your local computer. If TWS asks to allow a local
  API connection, verify it is the bot you just started.

This tool defaults to localhost, client ID 17 and port 7497. It rejects sessions
containing accounts without the standard paper-account `DU` prefix. Other paper
account formats are unsupported in this version. The port alone does not prove
that an account is a paper account.

## 2. Install on Windows

Install Python **3.11 or newer** from python.org, and copy or clone this repository
to your computer. Open PowerShell in the repository's `traiding-bot` folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe bot.py account
```

No virtual-environment activation or PowerShell execution-policy change is needed.
Keep TWS running and logged in. No IBKR password is stored or passed to the bot.
Account output contains your account number; redact it before sharing logs.

## 3. Preview an order

```powershell
.\.venv\Scripts\python.exe bot.py order AAPL BUY 1 100
```

This qualifies the stock with IBKR and prints a local preview. It sends **no order**
and does not request a broker margin/commission simulation. The price is an
illustrative input, not a price recommendation or current quote. Orders use SMART
routing, USD by default, DAY duration and regular trading hours only. A limit
order can remain unfilled; market-data subscriptions are not needed to enter a
price manually, but broker account and instrument restrictions still apply.

## 4. Explicitly submit a paper order

When ready, uncheck **Read-Only API** in TWS and apply the settings. Choose your
symbol, side, quantity and limit price, preview them first, then add `--submit`:

```powershell
.\.venv\Scripts\python.exe bot.py order AAPL BUY 1 100 --submit
.\.venv\Scripts\python.exe bot.py orders
```

Confirm the order and status in TWS. Submission is not confirmation of a fill.
Orders can remain open after the script exits. If the connection fails during
submission, inspect TWS before trying again to avoid duplicate orders.

## 5. Cancel an open order

Use the returned order ID (replace `123` below):

```powershell
.\.venv\Scripts\python.exe bot.py cancel 123
.\.venv\Scripts\python.exe bot.py cancel 123 --submit
```

Cancellation only targets orders owned by this API client ID and selected account.
Use TWS to cancel orders entered elsewhere. A fill can occur before cancellation;
check the final status in TWS.

## Activity log and fills

Every command appends JSON records to `logs/activity.jsonl` beside `bot.py`.
Records include UTC time and a run ID. Order submissions also carry that run ID
in the IBKR order reference so you can correlate them with TWS. Logged events
include submission/cancellation intent, observed order status, broker messages,
and execution events received while the script is connected. Preview events
are labelled separately from submissions. An intent record alone does not prove
that IBKR accepted the request.

To retrieve executions available from TWS after a script has exited:

```powershell
.\.venv\Scripts\python.exe bot.py fills
Get-Content .\logs\activity.jsonl -Tail 20
```

The `fills` command prints executions and appends an execution snapshot. TWS
limits the available execution history; this is not a complete account statement.
Snapshots can repeat executions: use `execution_id` when reconciling them.
The CLI does not keep monitoring once it exits, so rerun `orders` and `fills`
to refresh observations, and use TWS statements for authoritative history.

Logs contain account identifiers and trading details. They are ignored by Git;
keep them private. A custom path goes before the command:

```powershell
.\.venv\Scripts\python.exe bot.py --log-file C:\Trading\activity.jsonl orders
```

An unwritable log stops a command before order submission. If a later write
fails, inspect TWS before retrying: the order may already have been submitted.

## Connection options and troubleshooting

Global options go **before** the command:

```powershell
.\.venv\Scripts\python.exe bot.py --port 7497 --client-id 17 account
.\.venv\Scripts\python.exe bot.py --account DU1234567 orders
```

- Connection refused/timeout: check TWS is running, API is enabled and the port
  matches. Do not open the port to the public internet.
- Client ID in use: stop the other bot process or choose a different ID. Use the
  original ID when cancelling that client's orders.
- Read-only error: submitting/cancelling requires Read-Only API to be unchecked.
- Rejected order: inspect broker messages and TWS; do not retry blindly.
- Multiple DU accounts: explicitly choose the intended account with `--account`.

## Validation status

Automated tests exercise paper-account rejection, numeric input validation and
preview behavior using mocks. Cloud validation cannot reach TWS on your Windows
computer. Actual account connectivity, order submission, fills and cancellation
must be verified locally. No orders were submitted during development.
