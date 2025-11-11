package com.trader.backendtrader.controller;

import com.trader.backendtrader.entity.VirtualPosition;
import com.trader.backendtrader.repository.VirtualPositionRepository;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/virtual/positions")
@CrossOrigin(origins = {"http://localhost:5173", "http://127.0.0.1:5173"})
public class PositionController {

    private final VirtualPositionRepository repo;

    public PositionController(VirtualPositionRepository repo) {
        this.repo = repo;
    }

    @GetMapping
    public List<VirtualPosition> list() {
        // demo user (id = 1). Adjust if you store the user id differently.
        return repo.findByUserId(1L);
    }
}
