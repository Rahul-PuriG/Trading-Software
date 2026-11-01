# IBKR paper trading — local Windows execution

## Six-month SPY backtest

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
