from datetime import datetime, timedelta, timezone
import unittest

from backtest import Bar
from fractal_structure import FractalStructureTracker, trace_structure
from internal_structure import InternalPullbackTracker


class FractalStructureTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2025, 1, 29, 12, tzinfo=timezone.utc)

    def bars(self, values):
        return [Bar(self.t + timedelta(hours=i), *value)
                for i, value in enumerate(values)]

    def rising_leg(self):
        return self.bars([
            (150.4, 150.8, 150.3, 150.65),
            (150.6, 150.7, 150.2, 150.4),
            (150.5, 151.2, 150.45, 151.1),
            (151.05, 151.5, 150.9, 151.35),
            (151.25, 151.3, 150.7, 150.95),
            (151.0, 151.8, 150.95, 151.65),
        ])

    def test_newest_low_wick_break_changes_fractal_not_internal_direction(self):
        bars = self.rising_leg() + [Bar(self.t + timedelta(hours=6),
                                       151.0, 151.1, 150.6, 150.9)]
        internal = InternalPullbackTracker('BUY', 152, 149, self.t, 60)
        result = trace_structure(bars, 'BUY', internal=internal)
        choch = next(e for e in result['fractal_events'] if e['event'] == 'fractal_choch')
        self.assertEqual(choch['broken_level'], 150.7)
        self.assertEqual(choch['confirmation_quality'], 'wick_only')
        self.assertGreater(bars[-1].low, 150.2)
        self.assertEqual(choch['direction'], 'SELL')
        self.assertEqual(internal.direction, 'BUY')
        self.assertEqual(internal.state, 'pullback')
        self.assertEqual(result['internal_events'][-1]['event'], 'internal_pullback_started')

    def test_bearish_mirror_uses_newest_high(self):
        bars = self.rising_leg() + [Bar(self.t + timedelta(hours=6),
                                       151.0, 151.1, 150.6, 150.9)]
        bars = [Bar(b.timestamp, 302-b.open, 302-b.low, 302-b.high, 302-b.close)
                for b in bars]
        result = trace_structure(bars, 'SELL')
        choch = next(e for e in result['fractal_events'] if e['event'] == 'fractal_choch')
        self.assertAlmostEqual(choch['broken_level'], 151.3)
        self.assertEqual(choch['direction'], 'BUY')
        self.assertEqual(choch['confirmation_quality'], 'wick_only')

    def test_touch_of_newest_low_is_not_a_break(self):
        bars = self.rising_leg() + [Bar(self.t + timedelta(hours=6),
                                       151.0, 151.1, 150.7, 150.9)]
        result = trace_structure(bars, 'BUY')
        self.assertFalse(any(e['event'] == 'fractal_choch' for e in result['fractal_events']))
        self.assertEqual(result['final_state']['fractal_direction'], 'BUY')

    def test_choch_reseeds_new_direction_and_return_uses_prior_leg_high(self):
        bars = self.rising_leg() + self.bars([
            (151.0, 151.1, 150.6, 150.9),
            (150.9, 151.0, 150.4, 150.6),
            (150.6, 151.9, 150.5, 151.85),
        ])
        bars = [Bar(self.t + timedelta(hours=i), b.open, b.high, b.low, b.close)
                for i, b in enumerate(bars)]
        result = trace_structure(bars, 'BUY')
        changes = [e for e in result['fractal_events'] if e['event'] == 'fractal_choch']
        self.assertEqual([e['direction'] for e in changes], ['SELL', 'BUY'])
        self.assertEqual(changes[0]['opposite_reference_price'], 151.8)
        self.assertEqual(changes[1]['broken_level'], 151.8)
        self.assertEqual(changes[1]['opposite_reference_price'], 150.4)
        self.assertEqual(changes[0]['new_A_start'], bars[6].timestamp.isoformat())

    def test_newer_bearish_sequence_reference_replaces_reversal_high(self):
        values = [
            (151.0, 151.1, 150.6, 150.9),
            (150.9, 151.0, 150.4, 150.6),
            (150.6, 151.2, 150.5, 151.0),
            (151.0, 151.1, 150.3, 150.4),
            (150.4, 151.3, 150.35, 151.0),
        ]
        bars = self.rising_leg() + self.bars(values)
        bars = [Bar(self.t + timedelta(hours=i), b.open, b.high, b.low, b.close)
                for i, b in enumerate(bars)]
        result = trace_structure(bars, 'BUY')
        changes = [e for e in result['fractal_events'] if e['event'] == 'fractal_choch']
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[1]['broken_level'], 151.2)
        self.assertLess(bars[-1].high, 151.8)

    def test_outside_choch_candle_halts_without_choosing_direction(self):
        bars = self.rising_leg() + [Bar(self.t + timedelta(hours=6),
                                       151.0, 151.9, 150.6, 151.0)]
        result = trace_structure(bars, 'BUY')
        self.assertFalse(result['complete'])
        self.assertEqual(result['final_state']['status'], 'review_required')
        self.assertEqual(result['final_state']['fractal_direction'], 'BUY')
        self.assertFalse(any(e['event'] == 'fractal_choch' for e in result['fractal_events']))

    def test_outside_confirmation_does_not_promote_a_reference(self):
        bars = self.bars([(8, 10, 7, 9), (8, 9, 6, 8), (8, 10.5, 5.5, 10)])
        tracker = FractalStructureTracker('BUY')
        for b in bars: state = tracker.feed(b)
        self.assertEqual(state['status'], 'review_required')
        self.assertIsNone(state['opposing_reference'])
        with self.assertRaises(RuntimeError):
            tracker.feed(Bar(self.t + timedelta(hours=3), 9, 11, 7, 10))

    def test_reference_known_at_is_not_its_past_origin(self):
        bars = self.rising_leg()
        result = trace_structure(bars, 'BUY')
        reference = result['final_state']['opposing_reference']
        self.assertEqual(reference['origin_candle_starts'], [bars[4].timestamp.isoformat()])
        self.assertEqual(reference['known_at'], (bars[5].timestamp + timedelta(hours=1)).isoformat())
        before = trace_structure(bars[:3], 'BUY')
        known = bars[2].timestamp + timedelta(hours=1)
        self.assertEqual(before['fractal_events'], [e for e in result['fractal_events']
                         if datetime.fromisoformat(e['known_at']) <= known])

    def test_invalid_input_does_not_advance_state(self):
        tracker = FractalStructureTracker('BUY')
        tracker.feed(self.rising_leg()[0])
        before = tracker.snapshot()
        for candle in [self.rising_leg()[0],
                       Bar(self.t + timedelta(hours=1), 151, 150, 149, 149.5)]:
            with self.assertRaises(ValueError): tracker.feed(candle)
            self.assertEqual(tracker.snapshot(), before)

    def test_internal_duration_mismatch_rejected(self):
        internal = InternalPullbackTracker('BUY', 152, 149, self.t, 240)
        with self.assertRaises(ValueError):
            trace_structure(self.rising_leg(), 'BUY', internal=internal)

    def test_context_mapper_rejects_M15(self):
        with self.assertRaises(ValueError): FractalStructureTracker('BUY',15)
        with self.assertRaises(ValueError): trace_structure(self.rising_leg(),'BUY',15)

    def test_four_hour_context_is_supported(self):
        bars=[Bar(self.t+timedelta(hours=4*i),b.open,b.high,b.low,b.close)
              for i,b in enumerate(self.rising_leg())]
        result=trace_structure(bars,'BUY',240)
        self.assertTrue(result['complete'])
        self.assertEqual(result['final_state']['context_timeframe_minutes'],240)

    def outside_evidence(self,order):
        start=self.t+timedelta(hours=2)
        values=[]
        for i in range(60):
            if i<10: value=(8,8.1,7.9,8)
            elif order=='up_first':
                if i==10:value=(8,10.5,8,10)
                elif i<20:value=(10,10,9.9,10)
                elif i==20:value=(10,10,5.5,7)
                elif i<59:value=(7,7.1,6.9,7)
                else:value=(7,10,7,10)
            elif order=='low_first':
                if i==10:value=(8,8,5.5,7)
                elif i<20:value=(7,7.1,6.9,7)
                elif i==20:value=(7,10.5,7,10)
                else:value=(10,10,9.9,10)
            else:
                value=(8,10.5,5.5,10) if i==10 else (10,10,9.9,10)
            values.append(Bar(start+timedelta(minutes=i),*value))
        return values

    def outside_bars(self):
        return self.bars([(8,10,7,9),(8,9,6,8),(8,10.5,5.5,10)])

    def test_high_first_then_low_is_bearish_choch(self):
        result=trace_structure(self.outside_bars(),'BUY',minutes=self.outside_evidence('up_first'))
        self.assertTrue(result['complete'])
        self.assertEqual(result['final_state']['fractal_direction'],'SELL')
        choch=result['fractal_events'][-1]
        self.assertEqual(choch['event'],'fractal_choch')
        self.assertEqual(choch['broken_level'],6)
        self.assertEqual(choch['opposite_reference_price'],10.5)

    def test_low_first_then_high_has_no_fractal_break(self):
        result=trace_structure(self.outside_bars(),'BUY',minutes=self.outside_evidence('low_first'))
        self.assertTrue(result['complete'])
        self.assertEqual(result['final_state']['fractal_direction'],'BUY')
        self.assertEqual(result['fractal_events'][-1]['event'],'outside_sequence_no_fractal_break')
        self.assertIsNone(result['final_state']['opposing_reference'])

    def test_bearish_outside_mirror(self):
        bars=[Bar(b.timestamp,22-b.open,22-b.low,22-b.high,22-b.close)
              for b in self.outside_bars()]
        minutes=[Bar(b.timestamp,22-b.open,22-b.low,22-b.high,22-b.close)
                 for b in self.outside_evidence('up_first')]
        result=trace_structure(bars,'SELL',minutes=minutes)
        self.assertTrue(result['complete'])
        self.assertEqual(result['final_state']['fractal_direction'],'BUY')

    def test_same_minute_crossings_remain_unresolved(self):
        result=trace_structure(self.outside_bars(),'BUY',minutes=self.outside_evidence('same_minute'))
        self.assertFalse(result['complete'])
        self.assertEqual(result['final_state']['halted_reason'],'both_first_crossings_in_same_minute')

    def test_missing_minute_evidence_cannot_choose_order(self):
        result=trace_structure(self.outside_bars(),'BUY',minutes=self.outside_evidence('up_first')[:-1])
        self.assertFalse(result['complete'])
        self.assertEqual(result['final_state']['halted_reason'],'incomplete_or_unordered_minute_evidence')

    def test_wrong_price_feed_evidence_cannot_choose_order(self):
        minutes=self.outside_evidence('up_first')
        b=minutes[-1];minutes[-1]=Bar(b.timestamp,b.open,10.1,b.low,10.1)
        result=trace_structure(self.outside_bars(),'BUY',minutes=minutes)
        self.assertFalse(result['complete'])
        self.assertEqual(result['final_state']['halted_reason'],'minute_and_context_OHLC_mismatch')


if __name__ == '__main__':
    unittest.main()
