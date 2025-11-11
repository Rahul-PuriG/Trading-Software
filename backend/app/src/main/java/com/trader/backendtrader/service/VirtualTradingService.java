package com.trader.backendtrader.service;

import com.trader.backendtrader.dto.PlaceOrderRequest;
import com.trader.backendtrader.dto.PlaceOrderResponse;
import com.trader.backendtrader.entity.OrderEntity;
import com.trader.backendtrader.entity.TradeEntity;
import com.trader.backendtrader.entity.UserAccount;
import com.trader.backendtrader.repository.OrderRepository;
import com.trader.backendtrader.repository.TradeRepository;
import com.trader.backendtrader.repository.UserAccountRepository;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;
import com.trader.backendtrader.entity.VirtualPosition;
import com.trader.backendtrader.repository.VirtualPositionRepository;


import java.math.BigDecimal;
import java.util.Optional;

@Service
public class VirtualTradingService {

  private final UserAccountRepository userRepo;
  private final OrderRepository orderRepo;
  private final TradeRepository tradeRepo;
  private final PriceCache priceCache;

private final VirtualPositionRepository posRepo;

public VirtualTradingService(UserAccountRepository userRepo,
                             OrderRepository orderRepo,
                             TradeRepository tradeRepo,
                             PriceCache priceCache,
                             VirtualPositionRepository posRepo) {
    this.userRepo = userRepo;
    this.orderRepo = orderRepo;
    this.tradeRepo = tradeRepo;
    this.priceCache = priceCache;
    this.posRepo = posRepo;
}


  // Simplified: one demo user for now
private UserAccount ensureDemoUser() {
    UserAccount u = userRepo.findByUsername("demo")
        .orElseGet(() -> {
            var newUser = new UserAccount();
            newUser.setUsername("demo");
            newUser.setDemoBalance(new BigDecimal("100000"));
            return userRepo.save(newUser);
        });

    if (u.getDemoBalance() == null) {
        u.setDemoBalance(new BigDecimal("100000"));
        userRepo.save(u);
    }
    return u;
}


  @Transactional
  public PlaceOrderResponse placeOrder(PlaceOrderRequest req) {
    UserAccount user = ensureDemoUser();

    var trade = new OrderEntity();
    order.setUserId(user.getId());
    order.setSymbol(req.getSymbol());
    order.setSide(req.getSide().toUpperCase());
    order.setType(req.getType().toUpperCase());
    order.setQuantity(req.getQuantity());
    order.setPrice(req.getPrice());
    order.setStatus("OPEN");
    order = orderRepo.save(order);

    // Simulated execution:
    BigDecimal last = Optional.ofNullable(priceCache.getLast(req.getSymbol()))
                       .orElse(req.getPrice()); // fallback for LIMIT

    boolean shouldFill = false;
    BigDecimal execPrice = last;

    if ("MARKET".equals(order.getType())) {
      shouldFill = last != null;
    } else { // LIMIT
      if ("BUY".equals(order.getSide())) {
        shouldFill = last != null && last.compareTo(order.getPrice()) <= 0;
        execPrice = order.getPrice();
      } else {
        shouldFill = last != null && last.compareTo(order.getPrice()) >= 0;
        execPrice = order.getPrice();
      }
    }

    if (!shouldFill) {
      order.setStatus("OPEN");
      orderRepo.save(order);
      return new PlaceOrderResponse(order.getId(), "OPEN", null, null,
              "Limit not reached yet, order left OPEN");
    }

    // Balance check and fill
    BigDecimal cost = execPrice.multiply(order.getQuantity()); // no fees for now
    if ("BUY".equals(order.getSide())) {
      if (user.getDemoBalance().compareTo(cost) < 0) {
        order.setStatus("REJECTED");
        orderRepo.save(order);
        return new PlaceOrderResponse(order.getId(), "REJECTED", null, null,
                "Insufficient demo balance");
      }
      user.setDemoBalance(user.getDemoBalance().subtract(cost));
    } else { // SELL adds balance
      user.setDemoBalance(user.getDemoBalance().add(cost));
    }
    userRepo.save(user);

    var trade = new TradeEntity();
    trade.setOrderId(order.getId());
    trade.setUserId(user.getId());
    trade.setExecutedPrice(execPrice);
    trade.setExecutedQty(order.getQuantity());
    tradeRepo.save(trade);

    order.setStatus("FILLED");
    orderRepo.save(order);

    updatePosition(user, order.getSymbol(), order.getSide(), order.getQuantity(), execPrice);


    return new PlaceOrderResponse(order.getId(), "FILLED", execPrice, order.getQuantity(), "Filled in demo mode");
  }

  private void updatePosition(UserAccount user, String symbol, String side, BigDecimal execQty, BigDecimal execPrice) {
    VirtualPosition pos = posRepo.findByUserIdAndSymbol(user.getId(), symbol)
            .orElseGet(() -> {
                VirtualPosition p = new VirtualPosition();
                p.setUserId(user.getId());
                p.setSymbol(symbol);
                return p;
            });

    BigDecimal size = pos.getSize();
    BigDecimal avg = pos.getAvgPrice();

    if ("BUY".equals(side)) {
        // new avg price = (old_size * avg + qty * price) / (old_size + qty)
        BigDecimal newSize = size.add(execQty);
        BigDecimal newAvg = (size.multiply(avg).add(execQty.multiply(execPrice)))
                .divide(newSize, 8, java.math.RoundingMode.HALF_UP);
        pos.setSize(newSize);
        pos.setAvgPrice(newAvg);
    } else {
        // SELL
        BigDecimal newSize = size.subtract(execQty);
        // realized PnL = (sell_price - avg) * qty
        BigDecimal realized = execPrice.subtract(avg).multiply(execQty);
        pos.setRealizedPnl(pos.getRealizedPnl().add(realized));
        pos.setSize(newSize.max(BigDecimal.ZERO)); // prevent negatives for now
    }

    // update unrealized pnl
    BigDecimal lastPrice = priceCache.getLast(symbol);
    if (lastPrice != null) {
        pos.setUnrealizedPnl(lastPrice.subtract(pos.getAvgPrice()).multiply(pos.getSize()));
    }

    pos.setUpdatedAt(java.time.Instant.now());
    posRepo.save(pos);
}


  public BigDecimal getDemoBalance() {
    return ensureDemoUser().getDemoBalance();
  }

  public BigDecimal deposit(BigDecimal amount) {
    UserAccount u = ensureDemoUser();
    u.setDemoBalance(u.getDemoBalance().add(amount));
    userRepo.save(u);
    return u.getDemoBalance();
  }

  public BigDecimal reset(BigDecimal newBalance) {
    UserAccount u = ensureDemoUser();
    u.setDemoBalance(newBalance);
    userRepo.save(u);
    return u.getDemoBalance();
  }
}
