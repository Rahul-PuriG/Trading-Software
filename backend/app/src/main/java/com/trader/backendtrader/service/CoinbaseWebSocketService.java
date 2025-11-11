package com.trader.backendtrader.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trader.backendtrader.model.Ticker;
import com.trader.backendtrader.config.WebSocketConfig;
import jakarta.annotation.PostConstruct;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.net.http.WebSocket.Listener;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.CompletableFuture;

@Service
public class CoinbaseWebSocketService {

    private static final String COINBASE_WS_URL = "wss://ws-feed.exchange.coinbase.com";
    private final ObjectMapper mapper = new ObjectMapper();

    @Autowired
    private PriceCache priceCache;

    @PostConstruct
    public void connect() {
        HttpClient client = HttpClient.newHttpClient();

        client.newWebSocketBuilder()
                .buildAsync(URI.create(COINBASE_WS_URL), new Listener() {

                    @Override
                    public void onOpen(WebSocket webSocket) {
                        System.out.println("✅ Connected to Coinbase WebSocket!");
                        String subscribeMsg = """
                            {
                                "type": "subscribe",
                                "channels": [{"name": "ticker", "product_ids": ["BTC-USD"]}]
                            }
                            """;
                        webSocket.sendText(subscribeMsg, true);
                        Listener.super.onOpen(webSocket);
                    }

                    @Override
                    public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
                        try {
                            
                            JsonNode node = mapper.readTree(data.toString());
                            if (node.has("type") && node.get("type").asText().equals("ticker")) {
                                if (node.has("price") && node.has("product_id")) {
                                    String price = node.get("price").asText();
                                    String productId = node.get("product_id").asText();
                                    String time = node.has("time") ? node.get("time").asText() : "";

                                    String json = String.format(
                                        "{\"productId\":\"%s\",\"price\":%s,\"time\":\"%s\"}",
                                        productId, price, time
                                    );
                                    priceCache.update(productId, new BigDecimal(price));

                                    // ✅ broadcast this price update to all frontend clients
                                    WebSocketConfig.broadcast(json);
                                    System.out.println("📤 Sent to frontend: " + json);
                                }
                            }
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                        return Listener.super.onText(webSocket, data, last);
                    }


                    @Override
                    public void onError(WebSocket webSocket, Throwable error) {
                        System.err.println("❌ WebSocket error: " + error.getMessage());
                        Listener.super.onError(webSocket, error);
                    }

                    @Override
                    public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
                        System.out.println("🔌 WebSocket closed: " + reason);
                        return CompletableFuture.completedFuture(null);
                    }
                });
    }
}
