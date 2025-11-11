package com.trader.backendtrader.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Data
@Table(name = "virtual_position")
public class VirtualPosition {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private String symbol;

    @Column(precision = 30, scale = 8)
    private BigDecimal size = BigDecimal.ZERO;   // positive = long, negative = short

    @Column(precision = 30, scale = 8)
    private BigDecimal avgPrice = BigDecimal.ZERO;

    @Column(precision = 30, scale = 8)
    private BigDecimal realizedPnl = BigDecimal.ZERO;

    @Column(precision = 30, scale = 8)
    private BigDecimal unrealizedPnl = BigDecimal.ZERO;

    private Instant updatedAt = Instant.now();
}
