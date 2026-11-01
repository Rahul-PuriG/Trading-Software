from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from swing_lc1 import Zone,LiquidityReference,scan_lc1,scan_lc1_candidates


class LC1CandidateConnectionTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,19,30,tzinfo=timezone.utc)
        self.zone=Zone('SELL',155.6,155.8,self.t-timedelta(hours=2))
        self.minutes=[Bar(self.t+timedelta(minutes=i),155.4,
                         155.65 if i==6 else 155.45,155.3,155.4) for i in range(15)]
        self.quarters=[Bar(self.t,155.4,155.65,155.3,155.4)]

    def candidate(self,price=155.5):
        return {'status':'qualified','side':'SELL','source_timeframe_minutes':15,
                'origin':(self.t-timedelta(hours=1)).isoformat(),
                'available_at':(self.t-timedelta(minutes=30)).isoformat(),
                'inducement_level':price,'prior_reference':(self.t-timedelta(hours=2)).isoformat()}

    def run_scan(self,candidates,quarters=None,approved=True):
        return scan_lc1_candidates(self.zone,candidates,self.minutes,
                                   self.quarters if quarters is None else quarters,approved)

    def test_multiple_points_same_candle_produce_one_signal_with_both_supports(self):
        result=self.run_scan([self.candidate(155.4),self.candidate(155.5)])
        self.assertEqual(len(result['signals']),1)
        self.assertEqual(len(result['signals'][0]['supporting_inducements']),2)
        self.assertEqual(result['signals'][0]['available_at'],(self.t+timedelta(minutes=15)).isoformat())

    def test_duplicate_reference_pairs_do_not_multiply_orders(self):
        first=self.candidate();later={**first,'available_at':(self.t-timedelta(minutes=15)).isoformat()}
        result=self.run_scan([later,first])
        self.assertEqual(result['distinct_qualified_points'],1)
        self.assertEqual(len(result['signals'][0]['supporting_inducements']),1)
        self.assertEqual(result['signals'][0]['supporting_inducements'][0]['available'],first['available_at'])

    def test_consumed_level_is_not_reused_at_a_later_touch(self):
        before=Bar(self.t-timedelta(minutes=15),155.4,155.55,155.3,155.4)
        result=self.run_scan([self.candidate()],[before]+self.quarters)
        self.assertEqual(result['signals'],[])
        self.assertEqual(result['excluded'][0]['reason'],'inducement_already_taken_before_setup_window')

    def test_future_and_review_candidates_cannot_generate_signal(self):
        event=self.candidate()
        future={**event,'available_at':(self.t+timedelta(minutes=15)).isoformat()}
        review={**event,'status':'review_required'}
        self.assertEqual(self.run_scan([future,review])['signals'],[])

    def test_timeframe_separation_is_enforced(self):
        with self.assertRaises(ValueError):
            self.run_scan([{**self.candidate(),'source_timeframe_minutes':60}])

    def test_context_approval_is_not_bypassed(self):
        self.assertEqual(self.run_scan([self.candidate()],approved=False)['signals'],[])

    def test_old_poi_touch_does_not_authorize_later_liquidation_far_outside_zone(self):
        prior_start=self.t-timedelta(minutes=15)
        before=[Bar(prior_start+timedelta(minutes=i),155.65,155.7,155.5,155.65)
                for i in range(15)]
        now=[Bar(self.t+timedelta(minutes=i),155.1,155.3,154.9,155.2)
             for i in range(15)]
        quarters=[Bar(prior_start,155.65,155.7,155.5,155.65),
                  Bar(self.t,155.1,155.3,154.9,155.2)]
        result=scan_lc1(self.zone,LiquidityReference(155.25,self.t),before+now,quarters,True)
        self.assertEqual(result['signals'],[])
        self.assertEqual(result['events'][-1]['event'],'liquidation_candle_outside_poi_requires_review')


if __name__=='__main__':unittest.main()
