import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { LineChart, Line, ResponsiveContainer } from "recharts";


import {
  getBalance,
  resetBalance,
  deposit,
  getQuote,
  placeOrder,
  getOrders,
  getTrades,
} from "./api";

// ---------------- HEDGING MODE UNREALIZED PNL ------------------
function calculateHedgedPosition(openTrades, livePrice) {
  if (!livePrice) {
    return { size: 0, avgPrice: 0, upnl: 0 };
  }

  let size = 0;
  let weightedValue = 0;
  let upnl = 0;

  for (const t of openTrades) {
    if (t.pending) continue; // skip pending limit orders

    const entry = Number(t.executedPrice);
    const qty = Number(t.executedQty);
    const side = t.side;

    // hedging mode size
    size += side === "BUY" ? qty : -qty;

    // for avg price display (optional)
    weightedValue += side === "BUY" ? entry * qty : -entry * qty;

    // individual UN-PNL
    if (side === "BUY") {
      upnl += (livePrice - entry) * qty;
    } else {
      upnl += (entry - livePrice) * qty;
    }
  }

  let avgPrice = 0;
  if (size !== 0) {
    avgPrice = weightedValue / size;
  }

  return {
    size,
    avgPrice,
    upnl,
  };
}


const SYMBOL = "BTC-USD";

export default function TradingPanel() {
  const [balance, setBalance] = useState(null);
  const [price, setPrice] = useState(null);
  const [latestPriceWS, setLatestPriceWS] = useState(null);
  const [side, setSide] = useState("BUY");
  const [type, setType] = useState("MARKET");
  const [qty, setQty] = useState(0.001);
  const [limitPrice, setLimitPrice] = useState("");
  const [orders, setOrders] = useState([]);
  const [trades, setTrades] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState("");
  const [flash, setFlash] = useState(null); // ✨ for price flash

  const prevPriceRef = useRef(null); // ✨ store previous price

  function withLivePnl(positions, livePrice) {
    if (!livePrice) return positions;
    return positions.map((p) => {
      const size = Number(p.size ?? 0);
      const avg = Number(p.avgPrice ?? 0);
      const upnl = (livePrice - avg) * size;
      return { ...p, unrealizedPnl: upnl };
    });
  }

const refreshAll = async () => {
  try {
    const [b, q, allOrders, openTrades, p] = await Promise.all([
      getBalance(),
      getQuote(SYMBOL),
      getOrders(), // we'll filter here
      axios.get("http://localhost:8080/api/virtual/trades/open"),
      axios.get("http://localhost:8080/api/virtual/positions"),
    ]);

    setBalance(b.data);
    setPrice(q.data?.lastPrice ?? null);
    setPositions(p.data);

    // Orders table shows only FILLED orders (your rule)
    const filledOrders = allOrders.data.filter(o => o.status === "FILLED");
    setOrders(filledOrders);

    // Trades table shows:
    //  - OPEN filled trades (from /trades/open)
    //  - OPEN LIMIT orders (pending), shown as "Pending"
    const pendingLimitAsTrades = allOrders.data
      .filter(o => o.status === "OPEN" && o.type === "LIMIT")
      .map(o => ({
        // Map to trade-like shape for UI
        id: `PENDING-${o.id}`,
        orderId: o.id,
        timestamp: o.createdAt,
        executedPrice: null,            // not filled
        executedQty: o.quantity,
        side: o.side,
        symbol: o.symbol,
        pending: true,                  // custom flag
        type: "LIMIT",
      }));

    const openExecutedTrades = openTrades.data.map(t => ({
      ...t,
      pending: false,
      type: "MARKET_OR_FILLED_LIMIT",
    }));

    setTrades([...openExecutedTrades, ...pendingLimitAsTrades]);
  } catch (e) {
    console.error(e);
    setNote("⚠️ Could not refresh data. Check backend connection.");
  }
};



  useEffect(() => {
    refreshAll();
    const id = setInterval(refreshAll, 5000);
    return () => clearInterval(id);
  }, []);

  // ✨ Live price updates with flash animation
  // ✨ Live price updates with flash animation + keep-alive
useEffect(() => {
  let ws;
  let pingTimer;

  function connectWS() {
    ws = new WebSocket("ws://localhost:8080/coinbase-stream");

    ws.onopen = () => {
      console.log("✅ Connected to price WS");

      // 🔁 Send a small ping every 30 seconds so Spring doesn't close the connection
      pingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 30000);
    };

    ws.onmessage = (evt) => {
      try {
        // skip pongs
        if (evt.data === "pong") return;
        const msg = JSON.parse(evt.data);
        if (msg.productId === SYMBOL && msg.price) {
          const newPrice = Number(msg.price);
          const prev = prevPriceRef.current;
          if (prev && newPrice !== prev) {
            setFlash(newPrice > prev ? "up" : "down");
            setTimeout(() => setFlash(null), 500);
          }
          prevPriceRef.current = newPrice;
          setLatestPriceWS(newPrice);
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    ws.onclose = () => {
      console.warn("❌ WS disconnected, retrying in 3s...");
      clearInterval(pingTimer);
      setTimeout(connectWS, 3000); // auto-reconnect
    };

    ws.onerror = (err) => {
      console.error("⚠️ WS error:", err);
      ws.close();
    };
  }

  connectWS();

  return () => {
    clearInterval(pingTimer);
    if (ws) ws.close();
  };
}, []);


async function closeTrade(id) {
  try {
    const res = await axios.post(`http://localhost:8080/api/virtual/trade/${id}/close`);
    alert(
      `Closed. PnL: $${Number(res.data.realizedPnl).toFixed(2)} | New Balance: $${Number(res.data.newBalance).toFixed(2)}`
    );
    await refreshAll();
  } catch (err) {
    alert("Close error: " + (err.response?.data || err.message));
  }
}

async function cancelOrder(id) {
  try {
    const res = await axios.delete(`http://localhost:8080/api/virtual/order/${id}/cancel`);
    alert(res.data || `Order ${id} cancelled`);
    await refreshAll();
  } catch (err) {
    alert("Cancel error: " + (err.response?.data || err.message));
  }
}








  const livePrice = latestPriceWS ?? (price ? Number(price) : null);
  const positionsLive = withLivePnl(positions, livePrice);

  const onPlaceOrder = async () => {
    setLoading(true);
    setNote("");
    try {
      const body = {
        symbol: SYMBOL,
        side,
        type,
        quantity: Number(qty),
        price: type === "LIMIT" ? Number(limitPrice || 0) : 0,
      };
      const res = await placeOrder(body);
      setNote(
        `Order ${res.data.orderId}: ${res.data.status} — ${
          res.data.executedPrice
            ? `@ $${Number(res.data.executedPrice).toFixed(2)}`
            : res.data.message || ""
        }`
      );
      await refreshAll();
    } catch (e) {
      console.error(e);
      setNote("❌ Order failed");
    } finally {
      setLoading(false);
    }
  };

  const onReset = async () => {
    setLoading(true);
    try {
      await resetBalance(100000);
      setNote("✅ Balance reset to $100,000");
      await refreshAll();
    } catch (e) {
      console.error(e);
      setNote("❌ Reset failed");
    } finally {
      setLoading(false);
    }
  };

  const onDeposit = async (amt) => {
    setLoading(true);
    try {
      await deposit(amt);
      setNote(`💰 Deposited $${amt}`);
      await refreshAll();
    } catch (e) {
      console.error(e);
      setNote("❌ Deposit failed");
    } finally {
      setLoading(false);
    }
  };



  return (
    <div style={styles.wrap}>
      <h1>💹 Demo Trading — {SYMBOL}</h1>

      <div style={styles.row}>
        <div style={styles.card}>
          <h3>Account</h3>
          <p>
            Balance:{" "}
            {balance !== null ? `$${Number(balance).toFixed(2)}` : "Loading..."}
          </p>
          <div style={styles.btnRow}>
            <button onClick={onReset} disabled={loading} style={styles.btn}>
              Reset $100k
            </button>
            <button
              onClick={() => onDeposit(1000)}
              disabled={loading}
              style={styles.btnOutline}
            >
              +$1,000
            </button>
            <button
              onClick={() => onDeposit(10000)}
              disabled={loading}
              style={styles.btnOutline}
            >
              +$10,000
            </button>
          </div>
        </div>

        <div style={styles.card}>
          <h3>Market</h3>
          <p
            className={
              flash === "up"
                ? "flash-green"
                : flash === "down"
                ? "flash-red"
                : ""
            }
          >
            Live Price:{" "}
            {livePrice ? `$${livePrice.toFixed(2)}` : "Waiting for feed..."}
          </p>
          <small style={{ opacity: 0.7 }}>Updates live via WebSocket</small>
        </div>
      </div>

      <div style={styles.card}>
        <h3>Place Order</h3>
        <div style={styles.formRow}>
          <label>Side</label>
          <select
            value={side}
            onChange={(e) => setSide(e.target.value)}
            style={styles.input}
          >
            <option>BUY</option>
            <option>SELL</option>
          </select>

          <label>Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            style={styles.input}
          >
            <option>MARKET</option>
            <option>LIMIT</option>
          </select>

          <label>Qty</label>
          <input
            type="number"
            min="0"
            step="0.000001"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            style={styles.input}
          />

          {type === "LIMIT" && (
            <>
              <label>Limit Price</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                style={styles.input}
              />
            </>
          )}

          <button
            onClick={onPlaceOrder}
            disabled={loading}
            style={{
              ...styles.buyBtn,
              background: side === "BUY" ? "#22c55e" : "#ef4444",
            }}
          >
            {side}
          </button>
        </div>
        {note && <p style={{ marginTop: 8 }}>{note}</p>}
      </div>

      <div style={styles.row}>
<div style={{ ...styles.scrollCard, flex: 1 }}>
  <h3>Orders</h3>
  <div style={styles.tableWrapper}>
    <table style={styles.tableWide}>
      <thead>
        <tr>
          <th>ID</th><th>Time</th><th>Side</th><th>Type</th>
          <th>Qty</th><th>Price</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((o) => (
          <tr key={o.id}>
            <td>{o.id}</td>
            <td>{new Date(o.createdAt).toLocaleTimeString()}</td>
            <td>{o.side}</td>
            <td>{o.type}</td>
            <td>{o.quantity}</td>
            <td>{o.price ?? "-"}</td>
            <td>{o.status}</td>
            <td>
              
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</div>



{/* ---- Trades ---- */}
{/* ---- Open Trades (executed + pending limits) ---- */}
<div style={{ ...styles.scrollCard, flex: 1 }}>
  <h3>Open Trades</h3>
  <div style={styles.tableWrapper}>
    <table style={styles.tableWide}>
      <thead>
        <tr>
          <th>ID</th>
          <th>Order</th>
          <th>Side</th>
          <th>Type</th>
          <th>Time</th>
          <th>Price</th>
          <th>Qty</th>
          <th>Unrealized PnL ($)</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {trades.map((t) => {
          const current = Number(latestPriceWS ?? price ?? 0);
          const exec = t.executedPrice != null ? Number(t.executedPrice) : null;
          const qty = Number(t.executedQty ?? 0);
          const side = t.side || (orders.find(o => o.id === t.orderId)?.side) || "BUY";

          // UN-PNL only for executed trades
          let upnl = null;
          if (!t.pending && exec != null) {
            upnl = (side === "BUY" ? (current - exec) : (exec - current)) * qty;
          }

          return (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.orderId}</td>
              <td>{side}</td>
              <td>{t.pending ? `PENDING ${t.type}` : "FILLED"}</td>
              <td>{new Date(t.timestamp).toLocaleTimeString()}</td>
              <td>{exec != null ? exec.toFixed(2) : "—"}</td>
              <td>{qty}</td>
              <td style={{ color: upnl != null && upnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                {upnl != null ? upnl.toFixed(2) : "—"}
              </td>
              <td>
                {t.pending ? (
                  <button
                    onClick={() => cancelOrder(t.orderId)}
                    style={{ background: "#a3a3a3", color: "#000", border: "none", padding: "4px 10px", borderRadius: 6, cursor: "pointer" }}
                  >
                    Cancel
                  </button>
                ) : (
                  <button
                    onClick={() => closeTrade(t.id)}
                    style={{ background: "#ef4444", color: "#fff", border: "none", padding: "4px 10px", borderRadius: 6, cursor: "pointer" }}
                  >
                    Close
                  </button>
                )}
              </td>
            </tr>
          );
        })}
        {trades.length === 0 && (
          <tr><td colSpan={9} style={{ opacity: 0.6, padding: 8 }}>No open trades</td></tr>
        )}
      </tbody>
    </table>
  </div>
</div>




      </div>

      <div style={styles.card}>
        <h3>
          Positions{" "}
          {livePrice ? (
            <small style={{ opacity: 0.7 }}>• Live @ ${livePrice.toFixed(2)}</small>
          ) : null}
        </h3>

        {/* ➤ HEDGING CALC: Use open trades, not backend position */}
        {(() => {
          const hedged = calculateHedgedPosition(trades, livePrice);
          return (
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Size (hedged)</th>
                  <th>Avg Price</th>
                  <th>Unrealized PnL</th>
                  <th>Realized PnL</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{SYMBOL}</td>
                  <td>{hedged.size.toFixed(4)}</td>
                  <td>{hedged.avgPrice.toFixed(2)}</td>

                  <td
                    style={{
                      color: hedged.upnl >= 0 ? "#22c55e" : "#ef4444",
                      fontWeight: 600,
                    }}
                  >
                    {hedged.upnl.toFixed(2)}
                  </td>

                  <td style={{ color: "#3bc9db" }}>
                    {/* Realized PNL comes from backend */}
                    {positions?.[0]?.realizedPnl
                      ? Number(positions[0].realizedPnl).toFixed(2)
                      : "0.00"}
                  </td>
                </tr>
              </tbody>
            </table>
          );
        })()}
      </div>

    </div>
  );
}

// ---- Styles ----
const styles = {
  wrap: {
    fontFamily: "Inter, Arial, sans-serif",
    width: "100%",
    maxWidth: "100vw",
    margin: 0,
    padding: "20px",
    color: "#fff",
    boxSizing: "border-box",
  },

  row: {
    display: "flex",
    gap: 16,
    marginBottom: 16,
    flexWrap: "wrap",
    width: "100%",
    justifyContent: "space-between",
  },

  card: {
    background: "#181a1f",
    border: "1px solid #2a2d34",
    borderRadius: 12,
    padding: 16,
    flex: 1,
    minWidth: 300,
    boxSizing: "border-box",
  },

tableWrapper: {
  overflowX: "auto",      // ✅ horizontal scroll
  overflowY: "auto",      // ✅ vertical scroll
  width: "100%",
  maxHeight: "300px",     // ✅ adjust height as needed (try 250–400px)
  boxSizing: "border-box",
},

tableWide: {
  minWidth: "1000px",     // ✅ triggers horizontal scroll
  borderCollapse: "collapse",
  color: "#fff",
},

scrollCard: {
  background: "#181a1f",
  border: "1px solid #2a2d34",
  borderRadius: 12,
  padding: 16,
  minWidth: 300,
  flex: 1,
  boxSizing: "border-box",
  display: "flex",
  flexDirection: "column",
  height: "400px",         // ✅ container height
},


  formRow: {
    display: "flex",
    gap: 12,
    alignItems: "center",
    flexWrap: "wrap",
  },

  input: {
    background: "#0f1115",
    border: "1px solid #2a2d34",
    color: "#fff",
    padding: "8px 10px",
    borderRadius: 8,
    minWidth: 120,
  },

  btnRow: { display: "flex", gap: 8 },

  btn: {
    padding: "8px 12px",
    borderRadius: 8,
    border: "none",
    background: "#3b82f6",
    color: "#fff",
    cursor: "pointer",
  },

  btnOutline: {
    padding: "8px 12px",
    borderRadius: 8,
    border: "1px solid #3b82f6",
    background: "transparent",
    color: "#3b82f6",
    cursor: "pointer",
  },

  buyBtn: {
    padding: "10px 14px",
    borderRadius: 8,
    border: "none",
    color: "#000",
    fontWeight: 700,
    cursor: "pointer",
  },
};

