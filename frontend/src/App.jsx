// src/App.jsx
import TradingPanel from "./TradingPanel";

function App() {
  return (
    <div style={{ background: "#0b0d12", minHeight: "100vh", paddingBottom: 40 }}>
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
