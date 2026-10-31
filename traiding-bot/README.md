# IBKR paper trading — local Windows execution

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
