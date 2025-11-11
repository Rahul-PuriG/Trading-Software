package com.trader.backendtrader.controller;

import com.trader.backendtrader.dto.PlaceOrderRequest;
import com.trader.backendtrader.dto.PlaceOrderResponse;
import com.trader.backendtrader.entity.OrderEntity;
import com.trader.backendtrader.entity.TradeEntity;
import com.trader.backendtrader.repository.OrderRepository;
import com.trader.backendtrader.repository.TradeRepository;
import com.trader.backendtrader.service.VirtualTradingService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/virtual")
@CrossOrigin(origins = "*")
public class VirtualTradingController {

  private final VirtualTradingService tradingService;
  private final OrderRepository orderRepo;
  private final TradeRepository tradeRepo;

  public VirtualTradingController(VirtualTradingService tradingService,
                                  OrderRepository orderRepo,
                                  TradeRepository tradeRepo) {
    this.tradingService = tradingService;
    this.orderRepo = orderRepo;
    this.tradeRepo = tradeRepo;
  }
  
@DeleteMapping("/order/{id}/cancel")
public ResponseEntity<?> cancelOrder(@PathVariable Long id) {
    Optional<OrderEntity> opt = orderRepo.findById(id);
    if (opt.isEmpty()) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body("Order " + id + " not found");
    }

    OrderEntity order = opt.get();
    if (!"OPEN".equalsIgnoreCase(order.getStatus())) {
        return ResponseEntity.badRequest()
                .body("Only OPEN orders can be cancelled");
    }

    order.setStatus("CANCELLED");
    orderRepo.save(order);

    return ResponseEntity.ok("Order " + id + " cancelled successfully");
}



  @GetMapping("/balance")
  public ResponseEntity<BigDecimal> balance() {
    return ResponseEntity.ok(tradingService.getDemoBalance());
  }

  @PostMapping("/deposit")
  public ResponseEntity<BigDecimal> deposit(@RequestParam BigDecimal amount) {
    return ResponseEntity.ok(tradingService.deposit(amount));
  }

  @PostMapping("/reset")
  public ResponseEntity<BigDecimal> reset(@RequestParam BigDecimal amount) {
    return ResponseEntity.ok(tradingService.reset(amount));
  }

  @PostMapping("/order")
  public ResponseEntity<PlaceOrderResponse> placeOrder(@RequestBody PlaceOrderRequest req) {
    return ResponseEntity.ok(tradingService.placeOrder(req));
  }

  @GetMapping("/orders")
  public ResponseEntity<List<OrderEntity>> orders() {
    // demo user only
    return ResponseEntity.ok(orderRepo.findByUserIdOrderByCreatedAtDesc(1L));
  }

  @GetMapping("/trades")
  public ResponseEntity<List<TradeEntity>> trades() {
    return ResponseEntity.ok(tradeRepo.findByUserIdOrderByTimestampDesc(1L));
  }
}
