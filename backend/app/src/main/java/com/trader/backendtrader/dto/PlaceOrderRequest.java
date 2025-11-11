package com.trader.backendtrader.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class PlaceOrderRequest {
  private String symbol;      // e.g., BTC-USD
  private String side;        // BUY/SELL
  private String type;        // MARKET/LIMIT
  private BigDecimal quantity;
  private BigDecimal price;   // optional when MARKET
}
