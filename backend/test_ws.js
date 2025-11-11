const WebSocket = require("ws");
const ws = new WebSocket("ws://localhost:8080/coinbase-stream");

ws.on("open", () => console.log("✅ Connected manually to backend WebSocket!"));
ws.on("error", (err) => console.error("❌ Connection error:", err.message));
ws.on("close", () => console.log("🔌 Connection closed"));

