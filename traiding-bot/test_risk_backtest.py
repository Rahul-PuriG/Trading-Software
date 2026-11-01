from datetime import date, datetime, timedelta
import unittest

from backtest import Bar, NY
from risk_backtest import simulate_risk


class RiskBacktestTests(unittest.TestCase):
    def run_case(self, following, **settings):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        bars = [Bar(opening, 100, 100, 100, 100)]
        bars += [Bar(opening + timedelta(minutes=5*(i+1)), *prices)
                 for i, prices in enumerate(following)]
        signals = {opening + timedelta(minutes=5): ("BUY", 99)}
        return simulate_risk(bars, signals, date(2026, 5, 1), date(2026, 5, 2), **settings)

    def test_stop_sizes_one_percent_including_fees(self):
        summary, trades, _ = self.run_case([(100, 101, 98, 99)], commission=1, slippage_bps=0)
        self.assertEqual(trades[0]["quantity"], 98)
        self.assertEqual(trades[0]["planned_stop_risk"], 100)
        self.assertEqual(trades[0]["net_pnl"], -100)
        self.assertAlmostEqual(summary["net_pnl"], -100)

    def test_target_is_3_point_3_price_r(self):
        _, trades, _ = self.run_case([(100, 104, 100, 103)], commission=0, slippage_bps=0)
        self.assertEqual(trades[0]["exit_reason"], "target")
        self.assertAlmostEqual(trades[0]["target_price"], 103.3)
        self.assertAlmostEqual(trades[0]["net_r"], 3.3)

    def test_both_levels_touched_assumes_stop_first(self):
        summary, trades, _ = self.run_case([(100, 104, 98, 100)], commission=0, slippage_bps=0)
        self.assertEqual(trades[0]["exit_reason"], "stop")
        self.assertEqual(summary["ambiguous_5min_bars_stop_first"], 1)

    def test_gap_loss_can_exceed_risk_budget(self):
        _, trades, _ = self.run_case([(100, 100.5, 99.5, 100), (95, 96, 94, 95)],
                                     commission=0, slippage_bps=0)
        self.assertEqual(trades[0]["exit_reason"], "gap_stop")
        self.assertEqual(trades[0]["net_pnl"], -500)

    def test_capital_limits_quantity(self):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        bars = [Bar(opening, 100, 100, 100, 100),
                Bar(opening + timedelta(minutes=5), 100, 100, 100, 100)]
        summary, trades, _ = simulate_risk(bars, {opening+timedelta(minutes=5): ("BUY", 99.99)},
            date(2026, 5, 1), date(2026, 5, 2), commission=0, slippage_bps=0)
        self.assertEqual(trades[0]["quantity"], 100)
        self.assertLessEqual(trades[0]["planned_stop_risk"], 100)
        self.assertEqual(summary["cash_capped_entries"], 1)

    def test_no_fill_on_signal_bar_and_gap_below_stop_skips(self):
        summary, trades, _ = self.run_case([(98, 98, 97, 98)], commission=0)
        self.assertEqual(trades, [])
        self.assertEqual(summary["skipped_entries"], 1)

    def test_crossover_exits_before_intrabar_target(self):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        bars = [Bar(opening, 100, 100, 100, 100),
                Bar(opening+timedelta(minutes=5), 100, 101, 99.5, 100),
                Bar(opening+timedelta(minutes=10), 101, 105, 100, 104)]
        signals = {opening+timedelta(minutes=5): ("BUY", 99),
                   opening+timedelta(minutes=10): ("SELL", None)}
        _, trades, _ = simulate_risk(bars, signals, date(2026, 5, 1), date(2026, 5, 2),
                                     commission=0, slippage_bps=0)
        self.assertEqual(trades[0]["exit_reason"], "crossover")
        self.assertEqual(trades[0]["exit_price"], 101)

    def test_sizing_recalculates_after_profit(self):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        bars = [Bar(opening,100,100,100,100)]
        bars += [Bar(opening+timedelta(minutes=5*i),100,104,100,103.3) for i in (1,2)]
        signals = {opening+timedelta(minutes=5*i): ("BUY",99) for i in (1,2)}
        _, trades, _ = simulate_risk(bars, signals, date(2026,5,1), date(2026,5,2),
                                     commission=0, slippage_bps=0)
        self.assertEqual([t["quantity"] for t in trades], [100,103])
        self.assertAlmostEqual(trades[1]["risk_budget"], 103.3)


if __name__ == "__main__":
    unittest.main()
