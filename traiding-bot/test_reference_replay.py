from datetime import datetime, timedelta, timezone
import unittest

from backtest import Bar
from reference_replay import replay


class ReferenceReplayTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2025,1,23,14,30,tzinfo=timezone.utc)
        self.signal = Bar(self.t, 150, 151, 149, 150)

    def test_entry_cannot_use_signal_bar_before_close(self):
        before = Bar(self.t+timedelta(minutes=14), 149, 150, 148, 149)
        after = Bar(self.t+timedelta(minutes=15), 150, 150, 149.5, 150)
        result = replay(self.signal, [before, after], spread_pips=0, slippage_pips=0)
        self.assertEqual(result["status"], "not_triggered_in_initial_window")

    def test_target_is_two_r(self):
        entry = Bar(self.t+timedelta(minutes=15), 150, 150, 148.5, 149)
        target = Bar(self.t+timedelta(minutes=16), 149, 150, 144, 145)
        r = replay(self.signal, [entry,target], spread_pips=0, slippage_pips=0)
        self.assertEqual(r["exit_reason"], "target")
        self.assertEqual(r["target_level"], 145)
        self.assertEqual(r["price_r_before_commission"], 2)
        self.assertEqual(r["entry_minute_halifax"], "2025-01-23T10:45:00-04:00")

    def test_both_levels_in_one_bar_uses_stop_and_flags_uncertainty(self):
        bars = [Bar(self.t+timedelta(minutes=15), 150, 150, 148.5, 149),
                Bar(self.t+timedelta(minutes=16), 149, 152, 144, 148)]
        r = replay(self.signal,bars,spread_pips=0,slippage_pips=0)
        self.assertEqual(r["exit_reason"], "stop")
        self.assertTrue(r["ambiguous_stop_target_bar"])

    def test_short_stop_uses_ask(self):
        bars = [Bar(self.t+timedelta(minutes=15), 149.1, 150, 148.9, 149),
                Bar(self.t+timedelta(minutes=16), 150, 150.996, 149.5, 150)]
        r = replay(self.signal,bars,spread_pips=1,slippage_pips=.1)
        self.assertEqual(r["exit_reason"], "stop")

    def test_long_uses_opposite_quote_sides(self):
        bars = [Bar(self.t+timedelta(minutes=15), 150, 151.1, 150, 151),
                Bar(self.t+timedelta(minutes=16), 151, 156, 150, 155)]
        r = replay(self.signal,bars,side="BUY",spread_pips=1,slippage_pips=.1)
        self.assertEqual(r["exit_reason"], "target")
        self.assertAlmostEqual(r["entry_price"],151.001)


if __name__ == "__main__":
    unittest.main()
