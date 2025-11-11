package com.trader.backendtrader.service;

import com.trader.backendtrader.entity.QuoteEntity;
import com.trader.backendtrader.repository.QuoteRepository;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class PriceCache {
  private final ConcurrentHashMap<String, BigDecimal> last = new ConcurrentHashMap<>();
  private final QuoteRepository quoteRepo;

  public PriceCache(QuoteRepository quoteRepo) { this.quoteRepo = quoteRepo; }

  public void update(String symbol, BigDecimal lastPrice) {
    last.put(symbol, lastPrice);
    var q = new QuoteEntity();
    q.setSymbol(symbol);
    q.setLastPrice(lastPrice);
    q.setUpdatedAt(Instant.now());
    quoteRepo.save(q);
  }

  public BigDecimal getLast(String symbol) { 
      return last.get(symbol); 
  }
}
