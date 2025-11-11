package com.trader.backendtrader.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name = "orders")
@Data
public class OrderEntity {
  @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  private Long userId;            // FK -> user_account.id
  private String symbol;          // e.g., BTC-USD
  private String side;            // BUY / SELL
  private String type;            // MARKET / LIMIT

  @Column(precision = 30, scale = 8)
  private BigDecimal price;       // nullable for MARKET

  @Column(precision = 30, scale = 8)
  private BigDecimal quantity;

  private String status;          // NEW / FILLED / CANCELLED / OPEN
  private Instant createdAt = Instant.now();
}
