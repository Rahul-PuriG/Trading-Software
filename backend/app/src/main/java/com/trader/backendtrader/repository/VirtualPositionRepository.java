package com.trader.backendtrader.repository;

import com.trader.backendtrader.entity.VirtualPosition;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.List;

public interface VirtualPositionRepository extends JpaRepository<VirtualPosition, Long> {
    Optional<VirtualPosition> findByUserIdAndSymbol(Long userId, String symbol);
    List<VirtualPosition> findByUserId(Long userId);
    Optional<VirtualPosition> findBySymbol(String symbol);
}
