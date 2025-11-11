package com.trader.backendtrader.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;

@Entity @Table(name = "user_account")
@Data
public class UserAccount {
  @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  private String username;
  private String apiKey;       // optional for later live trading
  private String passphrase;   // optional

  // Demo balance for fake trading
  @Column(precision = 30, scale = 8)
  private BigDecimal demoBalance = new BigDecimal("100000.00");

  private Instant createdAt = Instant.now();
}
