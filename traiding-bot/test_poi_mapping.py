from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from poi_mapping import map_poi_candidates
from structure_evidence import StructureReference


class POIMappingTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,1,tzinfo=timezone.utc)
        values=[(10,11,9,10),(10,15,10,12),(12,13,11,12),
                (12,12,9.8,10),(10.2,14,10.1,12),(12,13.8,10.2,12),
                (12,13,9.5,9.6),(9.6,9.9,8.5,8.8)]
        self.hours=[Bar(self.t+timedelta(hours=i),*v) for i,v in enumerate(values)]
        self.ref=StructureReference('internal','SELL',9,self.t+timedelta(hours=1))

    def quarters(self,bars):
        result=[]
        for b in bars:
            values=[(b.open,b.high,b.open,b.open),
                    (b.open,max(b.open,b.close),b.low,b.close),
                    (b.close,b.close,b.close,b.close),(b.close,b.close,b.close,b.close)]
            result.extend(Bar(b.timestamp+timedelta(minutes=15*i),*v) for i,v in enumerate(values))
        return result

    def map(self,bars=None,quarters=None):
        bars=self.hours if bars is None else bars
        return map_poi_candidates(bars,self.quarters(bars) if quarters is None else quarters,self.ref)

    def test_extreme_origin_is_selected_as_full_candle_without_color_filter(self):
        result=self.map()
        extreme=next(p for p in result['candidates'] if p['origin_pattern']=='leg_extreme')
        self.assertEqual(extreme['origin'],self.hours[1].timestamp.isoformat())
        self.assertEqual((extreme['low'],extreme['high']),(10,15))
        self.assertGreater(self.hours[1].close,self.hours[1].open)
        self.assertEqual(extreme['available_at'],(self.t+timedelta(hours=8)).isoformat())

    def test_mid_leg_sweep_source_and_multiple_zones_retained(self):
        candidates=self.map()['candidates']
        middle=next(p for p in candidates if p['origin']==self.hours[4].timestamp.isoformat())
        self.assertEqual(middle['origin_pattern'],'mid_leg')
        self.assertTrue(middle['sweep_backed'])
        self.assertTrue(any(e['price']==13 for e in middle['sweep_evidence']))
        self.assertGreater(len(candidates),2)
        self.assertTrue(all(p['probability_grade'] is None for p in candidates))

    def test_buy_mirror_selects_full_demand_candle(self):
        bars=[Bar(b.timestamp,40-b.open,40-b.low,40-b.high,40-b.close) for b in self.hours]
        ref=StructureReference('internal','BUY',31,self.ref.known_at)
        result=map_poi_candidates(bars,self.quarters(bars),ref)
        extreme=next(p for p in result['candidates'] if p['origin_pattern']=='leg_extreme')
        self.assertEqual((extreme['low'],extreme['high']),(25,30))

    def test_wick_only_internal_break_does_not_create_confirmed_zone(self):
        bars=self.hours[:];b=bars[-1];bars[-1]=Bar(b.timestamp,b.open,b.high,b.low,9.2)
        self.assertEqual(self.map(bars)['status'],'awaiting_close_break')

    def test_future_candles_do_not_change_confirmed_origins(self):
        before=self.map()
        bars=self.hours+[Bar(self.t+timedelta(hours=8),8.8,16,8,15)]
        self.assertEqual(before,self.map(bars))

    def test_return_after_departure_marks_pre_confirmation_mitigation(self):
        bars=self.hours[:];last=bars[-1]
        bars[-1]=Bar(last.timestamp,last.open,10.05,last.low,last.close)
        quarters=self.quarters(bars)
        index=4*7;b=quarters[index]
        quarters[index]=Bar(b.timestamp,b.open,10.05,b.low,b.close)
        result=self.map(bars,quarters)
        extreme=next(p for p in result['candidates'] if p['origin_pattern']=='leg_extreme')
        self.assertEqual(extreme['freshness']['status'],'mitigated_before_confirmation')

    def test_far_edge_failure_before_break_is_reported(self):
        result=self.map()
        old=next(p for p in result['candidates']+result['excluded_candidates']
                 if p['origin']==self.hours[2].timestamp.isoformat())
        self.assertEqual(old['freshness']['status'],'invalid_before_confirmation')

    def test_user_A_origin_retained_and_adjacent_contained_B_excluded(self):
        values=[(10,11,9,10),(10.2,13,10,12),(12,12.9,10.1,11),(11,11.5,8.5,8.8)]
        bars=[Bar(self.t+timedelta(hours=i),*v) for i,v in enumerate(values)]
        result=self.map(bars)
        self.assertEqual([p['origin'] for p in result['candidates']],[bars[1].timestamp.isoformat()])
        excluded=result['excluded_candidates'][0]
        self.assertEqual(excluded['origin'],bars[2].timestamp.isoformat())
        self.assertEqual(excluded['retained_origin'],bars[1].timestamp.isoformat())

    def test_A_B_selection_is_mirrored_for_demand_origins(self):
        values=[(10,11,9,10),(10.2,13,10,12),(12,12.9,10.1,11),(11,11.5,8.5,8.8)]
        bars=[Bar(self.t+timedelta(hours=i),40-o,40-l,40-h,40-c)
              for i,(o,h,l,c) in enumerate(values)]
        ref=StructureReference('internal','BUY',31,self.ref.known_at)
        result=map_poi_candidates(bars,self.quarters(bars),ref)
        self.assertEqual([p['origin'] for p in result['candidates']],[bars[1].timestamp.isoformat()])
        self.assertEqual(len(result['excluded_candidates']),1)

    def test_missing_quotes_do_not_certify_freshness(self):
        quarters=self.quarters(self.hours);quarters.pop(4*6)
        extreme=next(p for p in self.map(quarters=quarters)['candidates'] if p['origin_pattern']=='leg_extreme')
        self.assertEqual(extreme['freshness']['status'],'quote_coverage_requires_review')

    def test_M15_context_and_fractal_reference_are_rejected(self):
        with self.assertRaises(ValueError):map_poi_candidates(self.hours,self.quarters(self.hours),self.ref,15)
        ref=StructureReference('fractal','SELL',9,self.ref.known_at)
        with self.assertRaises(ValueError):map_poi_candidates(self.hours,self.quarters(self.hours),ref)

    def test_unavailable_mapping_window_is_rejected(self):
        with self.assertRaises(ValueError):
            map_poi_candidates(self.hours,self.quarters(self.hours),self.ref,leg_start=self.t)


if __name__=='__main__':unittest.main()
