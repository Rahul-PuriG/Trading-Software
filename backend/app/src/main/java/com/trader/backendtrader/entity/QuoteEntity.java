package com.trader.backendtrader.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name = "quote")
@Data
public class QuoteEntity {
  @Id
  private String symbol; // PK (e.g., BTC-USD)

  @Column(precision = 30, scale = 8) private BigDecimal bid;
  @Column(precision = 30, scale = 8) private BigDecimal ask;
  @Column(precision = 30, scale = 8) private BigDecimal lastPrice;

  private Instant updatedAt = Instant.now();
}
