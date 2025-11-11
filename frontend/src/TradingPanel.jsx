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
      const [b, q, o, t, p] = await Promise.all([
        getBalance(),
        getQuote(SYMBOL),
        getOrders(),
        getTrades(),
        axios.get("http://localhost:8080/api/virtual/positions"),
      ]);
      setBalance(b.data);
      setPrice(q.data?.lastPrice ?? null);
      setOrders(o.data);
      setTrades(t.data);
      setPositions(p.data);
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


async function cancelOrder(id) {
  try {
    const res = await axios.delete(`http://localhost:8080/api/virtual/order/${id}/cancel`);
    alert(res.data || `Order ${id} cancelled`);
    await refreshAll();
  } catch (err) {
    console.error("Cancel error:", err);
    const msg = err.response?.data || err.message || "Unknown error";
    alert("Error cancelling order: " + msg);
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
        <div style={{ ...styles.card, flex: 1 }}>
          <h3>Orders</h3>
          <table style={styles.table}>
            <thead>
            <tr>
                <th>ID</th>
                <th>Time</th>
                <th>Side</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Status</th>
                <th>Action</th> {/* 👈 add this */}
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
                    {o.status === "OPEN" && (
                    <button
                        style={{
                        background: "#ef4444",
                        color: "#fff",
                        border: "none",
                        padding: "4px 8px",
                        borderRadius: 6,
                        cursor: "pointer",
                        }}
                        onClick={() => cancelOrder(o.id)}
                    >
                        Cancel
                    </button>
                    )}
                </td>
                </tr>
            ))}
            </tbody>

          </table>
        </div>

        <div style={{ ...styles.card, flex: 1 }}>
          <h3>Trades</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Order</th>
                <th>Time</th>
                <th>Price</th>
                <th>Qty</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.orderId}</td>
                  <td>{new Date(t.timestamp).toLocaleTimeString()}</td>
                  <td>{t.executedPrice}</td>
                  <td>{t.executedQty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={styles.card}>
        <h3>
          Positions{" "}
          {livePrice ? (
            <small style={{ opacity: 0.7 }}>• Live @ ${livePrice.toFixed(2)}</small>
          ) : null}
        </h3>
        <table style={styles.table}>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Size</th>
              <th>Avg Price</th>
              <th>Unrealized PnL</th>
              <th>Realized PnL</th>
            </tr>
          </thead>
          <tbody>
            {positionsLive.map((p) => {
              const upnl = Number(p.unrealizedPnl ?? 0);
              const realized = Number(p.realizedPnl ?? 0);
              const colorClass =
                upnl > 0 ? "flash-green" : upnl < 0 ? "flash-red" : "";
              return (
                <tr key={p.id}>
                  <td>{p.symbol}</td>
                  <td>{p.size}</td>
                  <td>{Number(p.avgPrice ?? 0).toFixed(2)}</td>
                                    <td className={colorClass} style={{ fontWeight: 600 }}>
                    {upnl.toFixed(2)}
                    <div style={{ width: 80, height: 30 }}>
                        <ResponsiveContainer>
                        <LineChart
                            data={[{ x: 0, y: 0 }, { x: 1, y: upnl }]}
                            margin={{ top: 0, bottom: 0, left: 0, right: 0 }}
                        >
                            <Line
                            type="monotone"
                            dataKey="y"
                            stroke={upnl >= 0 ? "#22c55e" : "#ef4444"}
                            strokeWidth={2}
                            dot={false}
                            />
                        </LineChart>
                        </ResponsiveContainer>
                    </div>
                  </td>

                  <td
                    style={{
                      color: realized >= 0 ? "#22c55e" : "#ef4444",
                    }}
                  >
                    {realized.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---- Styles ----
const styles = {
wrap: {
  fontFamily: "Inter, Arial, sans-serif",
  width: "100%",
  minHeight: "100vh",
  margin: 0,
  padding: "16px 24px",
  boxSizing: "border-box",
  backgroundColor: "#0b0d12",
  color: "#fff",
},

  row: { display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" },
  card: {
    background: "#181a1f",
    border: "1px solid #2a2d34",
    borderRadius: 12,
    padding: 16,
    minWidth: 300,
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
  table: { width: "100%", borderCollapse: "collapse" },
};
