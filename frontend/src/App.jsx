// src/App.jsx
import TradingPanel from "./TradingPanel";

function App() {
  return (
  <div
        style={{
          backgroundColor: "#0b0d12",
          color: "#fff",
          minHeight: "100vh",
          width: "100vw",            // ✅ Full width
          overflowX: "hidden",        // ✅ Prevent scrollbars
        }}
      >
      <div style={{ padding: 16 }}>
        <h1 style={{ color: "#fff", marginBottom: 8 }}>
          📊 Coinbase Live BTC/USD Trading Dashboard
        </h1>
      </div>

      <TradingPanel />
    </div>
  );
}

export default App;
