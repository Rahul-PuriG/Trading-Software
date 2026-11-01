"""USD account / USDJPY risk ledger. Pure simulation; no broker connection.

Gross fixed initial margin per trade, not broker netting. Mark equity using the
liquidation quote; omit uncharged exit fees until closing. JPY P&L converts to USD
at the exit quote. Financing, conversion fees and forced liquidation are absent.
"""

from dataclasses import dataclass
import math


def positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def direction(side):
    if side not in ("BUY", "SELL"):
        raise ValueError("Side must be BUY or SELL")
    return 1 if side == "BUY" else -1


def pnl_usd(side, units, entry, exit_price):
    positive(entry, "Entry")
    positive(exit_price, "Exit")
    return direction(side) * units * (exit_price - entry) / exit_price


@dataclass(frozen=True)
class Costs:
    spread_pips: float = 1.0
    slippage_pips: float = 0.1
    commission_min: float = 2.0
    commission_rate: float = 0.00002

    def __post_init__(self):
        for value in (self.spread_pips, self.slippage_pips, self.commission_min, self.commission_rate):
            if not math.isfinite(value) or value < 0:
                raise ValueError("Costs must be finite and nonnegative")

    def commission(self, units):
        return max(self.commission_min, units*self.commission_rate) if units else 0.0

    @property
    def slip(self):
        return self.slippage_pips * 0.01


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float

    def __post_init__(self):
        positive(self.bid, "Bid")
        positive(self.ask, "Ask")
        if self.bid > self.ask:
            raise ValueError("Bid cannot exceed ask")

    def liquidation(self, side):
        direction(side)
        return self.bid if side == "BUY" else self.ask


@dataclass(frozen=True)
class OrderPlan:
    side: str
    units: int
    entry_level: float
    stop_level: float
    expected_entry: float
    expected_stop_fill: float
    risk_budget: float
    planned_stop_risk: float
    available_at_plan: float
    reward_r: float
    margin: float


@dataclass(frozen=True)
class Position:
    trade_id: str
    side: str
    units: int
    entry: float
    stop: float
    target: float
    margin: float
    entry_commission: float
    planned_stop_risk: float
    risk_at_fill: float
    risk_budget: float


class FXAccount:
    def __init__(self, balance=10000.0, leverage=50.0, risk_fraction=0.01, costs=None):
        for name, value in [("Balance", balance), ("Leverage", leverage), ("Risk fraction", risk_fraction)]:
            positive(value, name)
        if risk_fraction > 1:
            raise ValueError("Risk fraction cannot exceed 1")
        self.balance = balance
        self.leverage = leverage
        self.risk_fraction = risk_fraction
        self.costs = costs or Costs()
        self.positions = {}
        self.closed = []

    @property
    def margin(self):
        return sum(p.margin for p in self.positions.values())

    def equity(self, quote):
        return self.balance + sum(pnl_usd(p.side,p.units,p.entry,quote.liquidation(p.side))
                                  for p in self.positions.values())

    def available(self, quote):
        return self.equity(quote) - self.margin

    def plan(self, side, entry_level, stop_level, quote, reward_r=2.0):
        sign = direction(side)
        for name, value in [("Entry level", entry_level), ("Stop level", stop_level), ("Reward R", reward_r)]:
            positive(value, name)
        if sign * (entry_level-stop_level) <= 0:
            raise ValueError("Protective stop is on the wrong side of entry")
        free = max(0.0, self.available(quote))
        budget = free * self.risk_fraction
        entry = entry_level + sign * self.costs.slip
        stop_fill = stop_level - sign * self.costs.slip
        positive(stop_fill, "Expected stop fill")
        positive(entry, "Expected entry")
        loss_per_unit = -pnl_usd(side,1,entry,stop_fill)
        # Quote at a hypothetical trigger, before market slippage. Reserve the
        # expected immediate spread/slippage loss as well as margin and entry fee.
        exit_at_trigger = entry_level - sign * self.costs.spread_pips * 0.01
        positive(exit_at_trigger, "Expected liquidation quote")
        initial_loss_per_unit = max(0.0,-pnl_usd(side,1,entry,exit_at_trigger))

        def permitted(units):
            fee = self.costs.commission(units)
            return (units*loss_per_unit + 2*fee <= budget + 1e-9
                    and units/self.leverage + fee + units*initial_loss_per_unit <= free + 1e-9)

        low, high = 0, math.floor(free*self.leverage)
        while low < high:
            candidate = (low+high+1)//2
            if permitted(candidate):
                low = candidate
            else:
                high = candidate-1
        units = low
        return OrderPlan(side, units, entry_level, stop_level, entry, stop_fill, budget,
                         units*loss_per_unit + 2*self.costs.commission(units), free,
                         reward_r, units/self.leverage)

    def open(self, trade_id, plan, fill_price, quote):
        if trade_id in self.positions or any(t["trade_id"] == trade_id for t in self.closed):
            raise ValueError("Trade ID must be unique")
        if plan.units < 1:
            raise ValueError("Insufficient available funds for minimum one-USD-unit simulation size")
        positive(fill_price, "Fill price")
        sign = direction(plan.side)
        if sign*(fill_price-plan.stop_level) <= 0:
            raise ValueError("Entry fill is beyond protective stop")
        fee = self.costs.commission(plan.units)
        initial_pnl = pnl_usd(plan.side,plan.units,fill_price,quote.liquidation(plan.side))
        if self.available(quote) - plan.margin - fee + initial_pnl < -1e-8:
            raise ValueError("Insufficient margin at fill; do not silently resize an existing order")
        actual_risk = -pnl_usd(plan.side,plan.units,fill_price,plan.expected_stop_fill) + 2*fee
        position = Position(trade_id,plan.side,plan.units,fill_price,plan.stop_level,
            fill_price+sign*plan.reward_r*abs(fill_price-plan.stop_level),plan.margin,
            fee,plan.planned_stop_risk,actual_risk,plan.risk_budget)
        positive(position.target, "Target")
        self.positions[trade_id] = position
        self.balance -= fee
        return position

    def close(self, trade_id, fill_price, reason):
        position = self.positions[trade_id]
        positive(fill_price, "Exit fill")
        fee = self.costs.commission(position.units)
        gross = pnl_usd(position.side,position.units,position.entry,fill_price)
        self.balance += gross - fee
        result = {"trade_id":trade_id,"side":position.side,"units":position.units,
            "entry_price":position.entry,"exit_price":fill_price,"exit_reason":reason,
            "gross_pnl_usd":gross,"commission_usd":position.entry_commission+fee,
            "net_pnl_usd":gross-position.entry_commission-fee,
            "risk_budget_usd":position.risk_budget,"planned_stop_risk_usd":position.planned_stop_risk,
            "risk_at_fill_usd":position.risk_at_fill,
            "risk_budget_exceeded_at_fill":position.risk_at_fill > position.risk_budget+1e-8,
            "released_margin_usd":position.margin}
        self.closed.append(result)
        del self.positions[trade_id]
        return result
