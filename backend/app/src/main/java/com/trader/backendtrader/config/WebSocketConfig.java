package com.trader.backendtrader.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private static final List<WebSocketSession> sessions = new CopyOnWriteArrayList<>();

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
    registry.addHandler(webSocketHandler(), "/coinbase-stream")
        .setAllowedOrigins("http://localhost:5173", "http://127.0.0.1:5173");
 // ✅ Allow all origins temporarily
    }

 @Bean
public TextWebSocketHandler webSocketHandler() {
    return new TextWebSocketHandler() {
        @Override
        public void afterConnectionEstablished(WebSocketSession session) {
            sessions.add(session);
            System.out.println("🔌 Frontend connected: " + session.getId());
        }

        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws IOException {
            if ("ping".equals(message.getPayload())) {
                session.sendMessage(new TextMessage("pong"));
                return;
            }
            // ignore or log other messages
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
            sessions.remove(session);
            System.out.println("❌ Frontend disconnected: " + session.getId());
        }
    };
}


    public static void broadcast(String message) {
        for (WebSocketSession session : sessions) {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
}
