from datetime import date, datetime, timedelta
import unittest

from backtest import Bar, NY, UTC, simulate, six_months_before, validate_coverage


class BacktestTests(unittest.TestCase):
    def bars(self, closes):
        first = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        warmup = [Bar(first - timedelta(days=1) + timedelta(minutes=5*i),
                      100, 100, 100, 100) for i in range(20)]
        active = [Bar(first + timedelta(minutes=5*i), 120 if i == 1 else c,
                      max(120 if i == 1 else c, c), min(120 if i == 1 else c, c), c)
                  for i, c in enumerate(closes)]
        return warmup + active

    def test_next_bar_fill_and_terminal_liquidation_with_costs(self):
        bars = self.bars([110, 111])
        summary, trades, _ = simulate(bars, date(2026, 5, 1), date(2026, 5, 2),
                                      commission=1, slippage_bps=10)
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual(trade["entry_time"], bars[-1].timestamp.isoformat())
        self.assertAlmostEqual(trade["entry_price"], 120 * 1.001)
        self.assertAlmostEqual(trade["exit_price"], 111 * .999)
        self.assertEqual(trade["exit_reason"], "end_of_test_liquidation")
        self.assertAlmostEqual(summary["net_pnl"], 111*.999 - 120*1.001 - 2)

    def test_no_crossover_means_no_trade(self):
        summary, trades, _ = simulate(self.bars([100]*30), date(2026, 5, 1), date(2026, 5, 2))
        self.assertEqual(trades, [])
        self.assertEqual(summary["net_pnl"], 0)
        self.assertIsNone(summary["win_rate_pct"])

    def test_last_bar_signal_cannot_fill_on_same_bar(self):
        _, trades, _ = simulate(self.bars([110]), date(2026, 5, 1), date(2026, 5, 2))
        self.assertEqual(trades, [])

    def test_future_bars_do_not_change_past_trades(self):
        bars = self.bars([110, 111] + [80]*20 + [120]*20)
        _, before, _ = simulate(bars, date(2026, 5, 1), date(2026, 5, 2))
        _, after, _ = simulate(bars + [Bar(datetime(2026, 5, 2, 9, 30, tzinfo=NY),
                                          900, 900, 900, 900)],
                               date(2026, 5, 1), date(2026, 5, 2))
        self.assertEqual(before, after)
        self.assertEqual(before[0]["exit_reason"], "crossover")

    def test_missing_bar_rejected_including_entire_session(self):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY).astimezone(UTC)
        sessions = [{"start": opening.isoformat(),
                     "end": (opening + timedelta(minutes=10)).isoformat()}]
        bars = [Bar(opening, 100, 100, 100, 100),
                Bar(opening + timedelta(minutes=5), 100, 100, 100, 100)]
        self.assertEqual(validate_coverage(bars, sessions, date(2026, 5, 1), date(2026, 5, 2)), 2)
        for incomplete in [bars[:1], []]:
            with self.assertRaises(ValueError):
                validate_coverage(incomplete, sessions, date(2026, 5, 1), date(2026, 5, 2))

    def test_calendar_month_range(self):
        self.assertEqual(six_months_before(date(2026, 11, 1)), date(2026, 5, 1))
        self.assertEqual(six_months_before(date(2026, 8, 31)), date(2026, 2, 28))


if __name__ == "__main__":
    unittest.main()
