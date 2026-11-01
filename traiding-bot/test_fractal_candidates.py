from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from fractal_candidates import detect_candidates,detect_sequence,FractalSequenceDetector


class FractalCandidateTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,12,tzinfo=timezone.utc)

    def bars(self,values):
        return [Bar(self.t+timedelta(minutes=15*i),*value) for i,value in enumerate(values)]

    def anchored(self,events,kind):
        return [e for e in events if e['anchor_start']==self.t.isoformat() and e['kind']==kind]

    def test_breaking_B_high_does_not_break_original_A(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(8,9.8,6.4,9)])
        self.assertEqual(self.anchored(detect_candidates(bars),'fractal_low_candidate'),[])

    def test_fixed_A_with_multiple_failures_retains_lowest_intervening_low(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(8,9.8,6.4,9),(9,10.2,6.5,9.9)])
        result=self.anchored(detect_candidates(bars),'fractal_low_candidate')[0]
        self.assertEqual(result['failed_candles'],2)
        self.assertEqual(result['reference_price'],6)
        self.assertEqual(result['reference_candle_starts'],[bars[1].timestamp.isoformat()])
        self.assertEqual(result['confirmation_quality'],'wick_only')

    def test_bearish_mirror_retains_highest_intervening_high(self):
        bars=self.bars([(12,13,10,11),(12,14,11,12),(12,13.5,10.5,11),(11,13,9.8,10.1)])
        result=self.anchored(detect_candidates(bars),'fractal_high_candidate')[0]
        self.assertEqual(result['reference_price'],14)
        self.assertEqual(result['failed_candles'],2)
        self.assertEqual(result['anchor_break_level'],10)

    def test_no_failed_candle_means_no_pullback(self):
        bars=self.bars([(8,10,7,9),(9,11,8,10)])
        self.assertEqual(self.anchored(detect_candidates(bars),'fractal_low_candidate'),[])

    def test_close_adds_quality_but_wick_stays_valid(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(9,10.2,6.5,10.1)])
        result=self.anchored(detect_candidates(bars),'fractal_low_candidate')[0]
        self.assertTrue(result['confirmation_candle_closed_beyond_A'])

    def test_reference_is_not_backdated_to_pullback_extreme(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(9,10.2,6.5,10.1)])
        result=self.anchored(detect_candidates(bars),'fractal_low_candidate')[0]
        self.assertEqual(result['available_at'],(bars[-1].timestamp+timedelta(minutes=15)).isoformat())

    def test_future_candles_do_not_rewrite_past_confirmations(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(9,10.2,6.5,10.1),(10,12,9,11)])
        before=detect_candidates(bars[:3]);after=detect_candidates(bars)
        known=(bars[2].timestamp+timedelta(minutes=15)).isoformat()
        self.assertEqual(before,[e for e in after if e['available_at']<=known])

    def test_equal_anchor_high_is_not_a_break(self):
        bars=self.bars([(8,10,7,9),(8,10,6,8),(9,10,6.5,9)])
        self.assertEqual(self.anchored(detect_candidates(bars),'fractal_low_candidate'),[])

    def test_confirmation_candle_crossing_reference_is_flagged(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(8,10.5,5.5,10)])
        result=self.anchored(detect_candidates(bars),'fractal_low_candidate')[0]
        self.assertTrue(result['requires_ordering_review'])

    def test_failed_candle_need_not_be_inside_A(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(9,10.5,6.5,10)])
        result=self.anchored(detect_candidates(bars),'fractal_low_candidate')[0]
        self.assertEqual(result['reference_price'],6)


class FractalSequenceTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,12,tzinfo=timezone.utc)

    def bars(self,values):
        return [Bar(self.t+timedelta(minutes=15*i),*value) for i,value in enumerate(values)]

    def illustrated_bars(self):
        return self.bars([
            (150.40,150.80,150.30,150.65),
            (150.60,150.70,150.20,150.40),
            (150.50,151.20,150.45,151.10),
            (151.05,151.50,150.90,151.35),
            (151.25,151.30,150.70,150.95),
            (151.00,151.80,150.95,151.65),
        ])

    def test_confirmed_ABC_then_DEF_example(self):
        bars=self.illustrated_bars()
        events=detect_sequence(bars,'BUY')
        self.assertEqual(len(events),2)
        self.assertEqual([e['anchor_start'] for e in events],
                         [bars[0].timestamp.isoformat(),bars[3].timestamp.isoformat()])
        self.assertEqual([e['reference_price'] for e in events],[150.20,150.70])
        self.assertEqual([e['confirmation_candle_start'] for e in events],
                         [bars[2].timestamp.isoformat(),bars[5].timestamp.isoformat()])
        self.assertTrue(all(e['confirmed'] for e in events))

    def test_bearish_mirror_advances_lower_lows_then_freezes(self):
        bars=[Bar(b.timestamp,302-b.open,302-b.low,302-b.high,302-b.close)
              for b in self.illustrated_bars()]
        events=detect_sequence(bars,'SELL')
        self.assertEqual(len(events),2)
        self.assertTrue(all(e['kind']=='fractal_high_confirmed' for e in events))
        self.assertAlmostEqual(events[0]['reference_price'],151.80)
        self.assertAlmostEqual(events[1]['reference_price'],151.30)
        self.assertEqual(events[1]['anchor_start'],bars[3].timestamp.isoformat())

    def test_nested_B_break_does_not_advance_frozen_A(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(8,9.8,6.4,9),(9,10.2,6.5,9.9)])
        events=detect_sequence(bars,'BUY')
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['anchor_start'],bars[0].timestamp.isoformat())
        self.assertEqual(events[0]['failed_candles'],2)
        self.assertEqual(events[0]['reference_price'],6)
        self.assertEqual(events[0]['confirmation_quality'],'wick_only')

    def test_C_can_be_the_frozen_A_for_the_very_next_pullback(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(9,11,7,10.5),
                        (10,10.8,8,10),(10,11.5,9,11.2)])
        events=detect_sequence(bars,'BUY')
        self.assertEqual(len(events),2)
        self.assertEqual(events[1]['anchor_start'],bars[2].timestamp.isoformat())
        self.assertEqual(events[1]['reference_price'],8)

    def test_uninterrupted_higher_highs_do_not_invent_pullbacks(self):
        bars=self.bars([(8,10,7,9),(9,11,8,10),(10,12,9,11)])
        self.assertEqual(detect_sequence(bars,'BUY'),[])

    def test_ambiguous_outside_C_is_flagged_not_confirmed(self):
        bars=self.bars([(8,10,7,9),(8,9,6,8),(8,10.5,5.5,10)])
        event=detect_sequence(bars,'BUY')[0]
        self.assertTrue(event['requires_ordering_review'])
        self.assertFalse(event['confirmed'])
        self.assertEqual(event['kind'],'fractal_low_candidate')

    def test_future_bars_do_not_rewrite_events_or_backdate_availability(self):
        bars=self.illustrated_bars()
        before=detect_sequence(bars[:3],'BUY');after=detect_sequence(bars,'BUY')
        known=(bars[2].timestamp+timedelta(minutes=15)).isoformat()
        self.assertEqual(before,[e for e in after if e['available_at']<=known])
        self.assertEqual(before[0]['available_at'],known)
        self.assertEqual(before[0]['reference_candle_starts'],[bars[1].timestamp.isoformat()])

    def test_equal_high_fails_and_retains_tied_extreme_origins(self):
        bars=self.bars([(8,10,7,9),(8,10,6,8),(8,9.5,6,9),(9,10.5,7,10.2)])
        event=detect_sequence(bars,'BUY')[0]
        self.assertEqual(event['anchor_start'],bars[0].timestamp.isoformat())
        self.assertEqual(event['failed_candles'],2)
        self.assertEqual(event['reference_candle_starts'],
                         [bars[1].timestamp.isoformat(),bars[2].timestamp.isoformat()])

    def test_quote_gap_is_reported_without_inventing_candles(self):
        bars=self.illustrated_bars()[:3]
        bars[2]=Bar(bars[2].timestamp+timedelta(minutes=15),
                    bars[2].open,bars[2].high,bars[2].low,bars[2].close)
        event=detect_sequence(bars,'BUY')[0]
        self.assertTrue(event['spans_quote_gap'])
        self.assertEqual(event['failed_candles'],1)

    def test_invalid_bar_cannot_move_anchor_or_advance_clock(self):
        detector=FractalSequenceDetector('BUY')
        first=self.illustrated_bars()[0]
        detector.feed(first)
        with self.assertRaises(ValueError):detector.feed(first)
        invalid=Bar(self.t+timedelta(minutes=15),150.6,150.7,150.65,150.68)
        with self.assertRaises(ValueError):detector.feed(invalid)
        self.assertEqual(detector.previous,first.timestamp)
        self.assertEqual(detector.anchor.candle,first)
        self.assertEqual(detector.anchor.failures,0)


if __name__=='__main__':unittest.main()
