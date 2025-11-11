package com.trader.backendtrader.repository;

import com.trader.backendtrader.entity.QuoteEntity;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface QuoteRepository extends JpaRepository<QuoteEntity, String> {

        Optional<QuoteEntity> findBySymbol(String symbol);

}
