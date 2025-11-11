package com.trader.backendtrader.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name = "trade")
@Data
public class TradeEntity {
  @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  private Long orderId; // FK -> orders.id
  private Long userId;

  @Column(precision = 30, scale = 8)
  private BigDecimal executedPrice;

  @Column(precision = 30, scale = 8)
  private BigDecimal executedQty;

  private Instant timestamp = Instant.now();
}
