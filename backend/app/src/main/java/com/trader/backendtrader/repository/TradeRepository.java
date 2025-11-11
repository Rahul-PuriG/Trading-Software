package com.trader.backendtrader.repository;

import com.trader.backendtrader.entity.TradeEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TradeRepository extends JpaRepository<TradeEntity, Long> {
  List<TradeEntity> findByUserIdOrderByTimestampDesc(Long userId);
}
