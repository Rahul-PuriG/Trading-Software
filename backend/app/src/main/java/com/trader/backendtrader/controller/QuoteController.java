package com.trader.backendtrader.controller;

import com.trader.backendtrader.entity.QuoteEntity;
import com.trader.backendtrader.repository.QuoteRepository;
import com.trader.backendtrader.service.PriceCache;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Optional;

@RestController
@RequestMapping("/api/quote")
@CrossOrigin(origins = {"http://localhost:5173", "http://127.0.0.1:5173"})
public class QuoteController {

    private final PriceCache priceCache;
    private final QuoteRepository quoteRepo;

    public QuoteController(PriceCache priceCache, QuoteRepository quoteRepo) {
        this.priceCache = priceCache;
        this.quoteRepo = quoteRepo;
    }

    // ✅ Return latest price directly from cache (fast)
    @GetMapping("/{symbol}")
    public ResponseEntity<?> getQuote(@PathVariable String symbol) {
        BigDecimal price = priceCache.getLast(symbol);
        if (price != null) {
            return ResponseEntity.ok()
                    .body(new QuoteEntity() {{
                        setSymbol(symbol);
                        setLastPrice(price);
                    }});
        }

        // fallback to DB if cache empty
        Optional<QuoteEntity> q = quoteRepo.findById(symbol);
        return q.<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }
}
