from datetime import datetime, timedelta, timezone
import unittest

from backtest import Bar
from inducement_candidates import detect_inducements, InducementCandidateDetector
from swing_lc1 import qualify_inducement


class InducementCandidateTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2025,1,29,12,tzinfo=timezone.utc)

    def bars(self, values):
        return [Bar(self.t+timedelta(minutes=15*i), *v) for i,v in enumerate(values)]

    def example(self):
        return self.bars([(10,11,9,10),(10,13,9.8,12),(12,12.5,9.7,11),
                          (11,12,9.5,10),(10,11.5,8.9,9.5)])

    def selected(self, events, bars, side='SELL'):
        return [e for e in events if e['side']==side and
                e['prior_reference']==bars[0].timestamp.isoformat() and e['status']=='qualified']

    def test_multiple_surviving_origins_retained_without_latest_only_filter(self):
        bars=self.example();events=self.selected(detect_inducements(bars),bars)
        self.assertEqual([e['inducement_level'] for e in events],[13,12.5,12])
        self.assertTrue(all(e['confirmation_quality']=='wick_only' for e in events))

    def test_buy_mirror_qualifies_lows_on_high_break(self):
        bars=[Bar(b.timestamp,24-b.open,24-b.low,24-b.high,24-b.close) for b in self.example()]
        events=self.selected(detect_inducements(bars),bars,'BUY')
        self.assertEqual([e['inducement_level'] for e in events],[11,11.5,12])

    def test_no_break_means_no_qualification(self):
        bars=self.example()[:-1]
        self.assertEqual(self.selected(detect_inducements(bars),bars),[])

    def test_reswept_origin_is_not_certified_at_a_later_break(self):
        bars=self.bars([(10,11,9,10),(10,12,9.8,11),(11,13,9.7,12),(12,12.5,8.9,9.5)])
        events=self.selected(detect_inducements(bars),bars)
        self.assertEqual([e['inducement_level'] for e in events],[13])

    def test_outside_break_is_review_required(self):
        bars=self.bars([(10,11,9,10),(10,12,9.8,11),(11,13,8.9,9.5)])
        event=next(e for e in detect_inducements(bars) if e['side']=='SELL' and
                   e['origin']==bars[1].timestamp.isoformat() and
                   e['prior_reference']==bars[0].timestamp.isoformat())
        self.assertEqual(event['status'],'review_required')

    def test_generated_pairs_match_independent_selected_reference_checker(self):
        bars=self.example();lookup={b.timestamp.isoformat():b for b in bars}
        for event in detect_inducements(bars):
            if event['status']!='qualified':continue
            check=qualify_inducement(bars,lookup[event['origin']],lookup[event['prior_reference']],event['side'])
            self.assertEqual(check['status'],'qualified')
            for key in ('available_at','confirmation_quality','broken_level'):
                self.assertEqual(event[key],check[key])

    def test_prefix_events_do_not_depend_on_later_prices(self):
        bars=self.example()
        after=bars+[Bar(self.t+timedelta(minutes=75),9.5,14,8,10)]
        known=bars[-1].timestamp+timedelta(minutes=15)
        self.assertEqual(detect_inducements(bars),[e for e in detect_inducements(after)
                         if datetime.fromisoformat(e['available_at'])<=known])

    def test_bad_bar_cannot_advance_clock(self):
        detector=InducementCandidateDetector();first=self.example()[0];detector.feed(first)
        with self.assertRaises(ValueError):detector.feed(first)
        with self.assertRaises(ValueError):
            detector.feed(Bar(self.t+timedelta(minutes=15),10,9,8,10))
        self.assertEqual(detector.previous,first.timestamp)


if __name__=='__main__':unittest.main()
