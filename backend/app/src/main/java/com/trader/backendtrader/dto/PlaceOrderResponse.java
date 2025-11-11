package com.trader.backendtrader.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.math.BigDecimal;

@Data @AllArgsConstructor
public class PlaceOrderResponse {
  private Long orderId;
  private String status;
  private BigDecimal executedPrice;
  private BigDecimal executedQty;
  private String message;
}
