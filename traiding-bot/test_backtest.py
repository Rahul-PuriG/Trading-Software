from datetime import date, datetime, timedelta
import unittest

from backtest import Bar, NY, UTC, aggregate_30min, simulate, six_months_before, validate_coverage


class BacktestTests(unittest.TestCase):
    def test_half_hour_aggregation_uses_session_open_and_last_close(self):
        first = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        source = [Bar(first + timedelta(minutes=5*i), 100+i, 102+i, 99+i, 101+i)
                  for i in range(12)]
        bars = aggregate_30min(source)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0], Bar(first, 100, 107, 99, 106))
        self.assertEqual(bars[1].timestamp, first + timedelta(minutes=30))
        with self.assertRaises(ValueError):
            aggregate_30min(source[:5] + source[6:])

    def test_aggregation_does_not_join_separate_days(self):
        first = datetime(2026, 5, 1, 15, 30, tzinfo=NY)
        second = datetime(2026, 5, 4, 9, 30, tzinfo=NY)
        source = [Bar(t + timedelta(minutes=5*i), 100, 100, 100, 100)
                  for t in [first, second] for i in range(6)]
        self.assertEqual([b.timestamp for b in aggregate_30min(source)], [first, second])

    def test_trend_filter_blocks_below_trend_and_allows_above(self):
        opening = datetime(2026, 5, 1, 9, 30, tzinfo=NY)
        def data(old_price):
            warmup = [Bar(opening - timedelta(days=10) + timedelta(minutes=30*i), p, p, p, p)
                      for i, p in enumerate([old_price]*70 + [100]*30)]
            return warmup + [Bar(opening, 110, 110, 110, 110),
                             Bar(opening + timedelta(minutes=30), 112, 113, 112, 113)]
        settings = dict(fast=10, slow=30, trend=100, bar_minutes=30)
        _, blocked, _ = simulate(data(200), date(2026, 5, 1), date(2026, 5, 2), **settings)
        _, allowed, _ = simulate(data(50), date(2026, 5, 1), date(2026, 5, 2), **settings)
        self.assertEqual(blocked, [])
        self.assertEqual(len(allowed), 1)
        self.assertEqual(allowed[0]["entry_time"], (opening + timedelta(minutes=30)).isoformat())

    def test_slow_strategy_requires_full_warmup(self):
        with self.assertRaisesRegex(ValueError, "100 pre-period"):
            simulate(self.bars([110,111]), date(2026, 5, 1), date(2026, 5, 2),
                     fast=10, slow=30, trend=100, bar_minutes=30)

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
