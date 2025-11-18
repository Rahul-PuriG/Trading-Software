package com.trader.backendtrader.controller;

import com.trader.backendtrader.dto.PlaceOrderRequest;
import com.trader.backendtrader.dto.PlaceOrderResponse;
import com.trader.backendtrader.entity.OrderEntity;
import com.trader.backendtrader.entity.TradeEntity;
import com.trader.backendtrader.repository.OrderRepository;
import com.trader.backendtrader.repository.TradeRepository;
import com.trader.backendtrader.repository.UserAccountRepository;
import com.trader.backendtrader.repository.VirtualPositionRepository;
import com.trader.backendtrader.service.PriceCache;
import com.trader.backendtrader.service.VirtualTradingService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/virtual")
@CrossOrigin(origins = "*")
public class VirtualTradingController {

  private final VirtualTradingService tradingService;
  private final OrderRepository orderRepo;
  private final TradeRepository tradeRepo;
  private final VirtualPositionRepository positionRepo;

  // ✅ add these
  private final UserAccountRepository userRepo;
  private final PriceCache priceCache;

  public VirtualTradingController(VirtualTradingService tradingService,
                                  OrderRepository orderRepo,
                                  TradeRepository tradeRepo,
                                  UserAccountRepository userRepo,
                                  PriceCache priceCache,
                                  VirtualPositionRepository positionRepo ) {
    this.tradingService = tradingService;
    this.orderRepo = orderRepo;
    this.tradeRepo = tradeRepo;
    this.userRepo = userRepo;
    this.priceCache = priceCache;
    this.positionRepo = positionRepo;
  }

  // -------- Account --------
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

  // -------- Orders --------
  @PostMapping("/order")
  public ResponseEntity<PlaceOrderResponse> placeOrder(@RequestBody PlaceOrderRequest req) {
    return ResponseEntity.ok(tradingService.placeOrder(req));
  }

  @GetMapping("/orders")
  public ResponseEntity<List<OrderEntity>> orders() {
    return ResponseEntity.ok(orderRepo.findByUserIdOrderByCreatedAtDesc(1L));
  }

  @DeleteMapping("/order/{id}/cancel")
  public ResponseEntity<?> cancelOrder(@PathVariable Long id) {
    Optional<OrderEntity> opt = orderRepo.findById(id);
    if (opt.isEmpty()) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Order " + id + " not found");
    }
    OrderEntity order = opt.get();
    if (!"OPEN".equalsIgnoreCase(order.getStatus())) {
      return ResponseEntity.badRequest().body("Only OPEN orders can be cancelled");
    }
    order.setStatus("CANCELLED");
    orderRepo.save(order);
    return ResponseEntity.ok("Order " + id + " cancelled successfully");
  }

  // -------- Trades --------

  // all trades (unchanged)
  @GetMapping("/trades")
  public ResponseEntity<List<TradeEntity>> trades() {
    return ResponseEntity.ok(tradeRepo.findByUserIdOrderByTimestampDesc(1L));
  }

  // ✅ only OPEN trades (for your new Open Trades table)
@GetMapping("/trades/open")
public ResponseEntity<List<TradeEntity>> openTrades() {
  return ResponseEntity.ok(tradeRepo.findByUserIdAndStatusOrderByTimestampDesc(1L, "OPEN"));
}


  // ✅ close a single trade: settle PnL to balance, mark CLOSED
@PostMapping("/trade/{id}/close")
public ResponseEntity<?> closeTrade(@PathVariable Long id) {
    var tradeOpt = tradeRepo.findById(id);
    if (tradeOpt.isEmpty()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Trade not found");

    var trade = tradeOpt.get();
    if (!"OPEN".equalsIgnoreCase(trade.getStatus())) {
        return ResponseEntity.badRequest().body("Trade already closed");
    }

    // original order to get side & symbol
    var order = orderRepo.findById(trade.getOrderId())
            .orElseThrow(() -> new RuntimeException("Order not found"));
    String side = order.getSide();
    String symbol = order.getSymbol();

    // user
    var user = userRepo.findById(trade.getUserId())
            .orElseThrow(() -> new RuntimeException("User not found"));

    // current market
    var current = Optional.ofNullable(priceCache.getLast(symbol))
            .orElse(trade.getExecutedPrice());

    var entry = trade.getExecutedPrice();
    var qty   = trade.getExecutedQty();

    // realized PnL per your spec
    // BUY: pnl = (current - entry)*qty; refund entry*qty back (spent at open)
    // SELL: pnl = (entry - current)*qty; remove entry*qty (was credited at open)
    BigDecimal pnl, balanceDelta;
    BigDecimal openCost = entry.multiply(qty);

    if ("BUY".equalsIgnoreCase(side) ) {
        pnl = current.subtract(entry).multiply(qty);
        balanceDelta = openCost.add(pnl);         // +amount used to open + pnl
    } else {
        pnl = entry.subtract(current).multiply(qty);
        balanceDelta = pnl.subtract(openCost);    // -amount used to open + pnl
    }

    // update balance
    user.setDemoBalance(user.getDemoBalance().add(balanceDelta));
    userRepo.save(user);

    // mark trade closed
    trade.setStatus("CLOSED");
    tradeRepo.save(trade);

    // update position UN-PNL / realized and size if no open trades remain
    positionRepo.findByUserIdAndSymbol(user.getId(), symbol).ifPresent(pos -> {
        // add realized pnl
        pos.setRealizedPnl(pos.getRealizedPnl().add(pnl));

        // if there are no more OPEN trades for this symbol, reset size & UN-PNL
        var stillOpenForSymbol = tradeRepo.findByUserIdAndStatusOrderByTimestampDesc(user.getId(), "OPEN")
                .stream()
                .anyMatch(t -> {
                    var o = orderRepo.findById(t.getOrderId()).orElse(null);
                    return o != null && symbol.equals(o.getSymbol());
                });

if (!stillOpenForSymbol) {
    // no open trades left -> fully closed
    pos.setUnrealizedPnl(BigDecimal.ZERO);
    pos.setSize(BigDecimal.ZERO);
} else {
    // some trades still open -> recompute partial unrealized PnL
    // collect all open trades for this symbol
    var openForSymbol = tradeRepo.findByUserIdAndStatusOrderByTimestampDesc(user.getId(), "OPEN")
        .stream()
        .filter(t -> {
            var o = orderRepo.findById(t.getOrderId()).orElse(null);
            return o != null && symbol.equals(o.getSymbol());
        })
        .toList();

    // calculate combined position size and weighted average price
    BigDecimal totalQty = BigDecimal.ZERO;
    BigDecimal weightedValue = BigDecimal.ZERO;
    for (var t : openForSymbol) {
        var o = orderRepo.findById(t.getOrderId()).orElse(null);
        if (o == null) continue;
        BigDecimal q = t.getExecutedQty();
        BigDecimal p = t.getExecutedPrice();
        if ("BUY".equalsIgnoreCase(o.getSide())) {
            totalQty = totalQty.add(q);
            weightedValue = weightedValue.add(p.multiply(q));
        } else {
            totalQty = totalQty.subtract(q);
            weightedValue = weightedValue.subtract(p.multiply(q));
        }
    }

    BigDecimal avgPrice = BigDecimal.ZERO;
    if (totalQty.compareTo(BigDecimal.ZERO) != 0) {
        avgPrice = weightedValue.divide(totalQty, 8, RoundingMode.HALF_UP);
    }

    BigDecimal last = Optional.ofNullable(priceCache.getLast(symbol)).orElse(avgPrice);
    BigDecimal diff = last.subtract(avgPrice);
    BigDecimal unrealized = diff.multiply(totalQty);

    pos.setSize(totalQty);
    pos.setAvgPrice(avgPrice);
   pos.setUnrealizedPnl(unrealized);
}
pos.setUpdatedAt(Instant.now());
positionRepo.save(pos);

    });

    return ResponseEntity.ok(Map.of(
            "tradeId", trade.getId(),
            "symbol", symbol,
            "side", side,
            "realizedPnl", pnl,
            "balanceDelta", balanceDelta,
            "newBalance", user.getDemoBalance()
    ));
}


}
