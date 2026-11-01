from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from swing_lc1 import Zone,LiquidityReference,zone_after_break,scan_lc1,trace_pending_entry,qualify_inducement


class LC1SequenceTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,19,30,tzinfo=timezone.utc)
        self.zone=Zone("SELL",155.6,155.8,self.t-timedelta(hours=2))
        self.liquidity=LiquidityReference(155.5,self.t-timedelta(hours=1))

    def minute_group(self):
        return [Bar(self.t+timedelta(minutes=i),155.4,155.65 if i==6 else 155.45,
                    155.3,155.4) for i in range(15)]

    def candle(self,minutes):
        return Bar(minutes[0].timestamp,minutes[0].open,max(b.high for b in minutes),
                   min(b.low for b in minutes),minutes[-1].close)

    def test_no_signal_before_liquidation_candle_closes(self):
        minutes=self.minute_group();quarter=self.candle(minutes)
        before=scan_lc1(self.zone,self.liquidity,minutes[:14],[quarter],True)
        self.assertEqual(before['signals'],[])
        after=scan_lc1(self.zone,self.liquidity,minutes,[quarter],True)
        self.assertEqual(after['signals'][0]['available_at'],(self.t+timedelta(minutes=15)).isoformat())

    def test_distance_is_reported_but_does_not_reject_entry(self):
        minutes=self.minute_group()
        far=LiquidityReference(155.0,self.t-timedelta(hours=1))
        result=scan_lc1(self.zone,far,minutes,[self.candle(minutes)],True)
        signal=result['signals'][0]
        self.assertEqual(signal['inducement_distance_to_poi_pips'],60)
        self.assertFalse(signal['proximity_is_entry_filter'])
        self.assertEqual(signal['inducement_timeframe_minutes'],15)

    def test_inducement_inside_poi_has_zero_distance(self):
        minutes=self.minute_group()
        inside=LiquidityReference(155.62,self.t-timedelta(hours=1))
        result=scan_lc1(self.zone,inside,minutes,[self.candle(minutes)],True)
        self.assertEqual(result['signals'][0]['inducement_distance_to_poi_pips'],0)

    def test_context_timeframe_cannot_supply_LC1_inducement(self):
        with self.assertRaises(ValueError):
            LiquidityReference(155.5,self.t,source_timeframe_minutes=60)

    def test_zone_wick_breach_removes_eligibility_without_close(self):
        minutes=self.minute_group();b=minutes[7]
        minutes[7]=Bar(b.timestamp,155.4,155.81,155.3,155.4)
        result=scan_lc1(self.zone,self.liquidity,minutes,[self.candle(minutes)],True)
        self.assertFalse(result['zone_valid']);self.assertEqual(result['signals'],[])

    def test_close_confirmation_not_backdated_to_origin(self):
        origin=Bar(self.t,155.6,155.8,155.5,155.7)
        wick=Bar(self.t+timedelta(hours=1),155.4,155.5,155,155.3)
        close=Bar(self.t+timedelta(hours=2),155.3,155.4,155,155.1)
        zone=zone_after_break([origin,wick,close],origin,155.2,'SELL')
        self.assertEqual(zone.available_at,self.t+timedelta(hours=3))

    def test_unavailable_liquidity_reference_cannot_generate_signal(self):
        minutes=self.minute_group()
        future=LiquidityReference(155.5,self.t+timedelta(hours=1))
        result=scan_lc1(self.zone,future,minutes,[self.candle(minutes)],True)
        self.assertEqual(result['signals'],[])

    def test_pre_touch_next_candle_wick_invalidates_sell_sequence(self):
        minutes=[Bar(self.t+timedelta(minutes=i),155.4,155.55,155.3,155.4) for i in range(15)]
        nextbar=Bar(self.t+timedelta(minutes=15),155.4,155.5,155.29,155.4)
        result=scan_lc1(self.zone,self.liquidity,minutes+[nextbar],[self.candle(minutes)],True)
        self.assertTrue(result['setup_early_invalidated']);self.assertTrue(result['zone_valid'])
        self.assertEqual(result['signals'],[])

    def test_context_not_approved_is_not_auto_overridden_by_lc(self):
        minutes=self.minute_group()
        self.assertEqual(scan_lc1(self.zone,self.liquidity,minutes,[self.candle(minutes)],False)['signals'],[])

    def test_pending_replacement_moves_both_levels_only_after_candle_close(self):
        active=self.t+timedelta(minutes=15)
        signal={'side':'SELL','available_at':active.isoformat(),'signal_bar_start':self.t.isoformat(),
                'entry_level':155.2,'stop_level':155.7}
        bars=[Bar(active+timedelta(minutes=i),155.4,155.65,155.3,155.4) for i in range(15)]
        quarter=Bar(active,155.4,155.65,155.3,155.4)
        result=trace_pending_entry(signal,self.zone,bars,[quarter])
        self.assertEqual(result['status'],'pending_at_data_end')
        amendment=result['events'][0]
        self.assertEqual(amendment['known_at'],(active+timedelta(minutes=15)).isoformat())
        self.assertEqual((amendment['entry_level'],amendment['stop_level']),(155.3,155.65))
        self.assertTrue(amendment['risk_recalculation_required'])

    def test_trigger_prevents_later_order_amendment(self):
        active=self.t+timedelta(minutes=15)
        signal={'side':'SELL','available_at':active.isoformat(),'signal_bar_start':self.t.isoformat(),
                'entry_level':155.3,'stop_level':155.7}
        bars=[Bar(active,155.4,155.65,155.29,155.4)]
        result=trace_pending_entry(signal,self.zone,bars,[])
        self.assertEqual(result['status'],'filled')
        self.assertFalse(any(e['event']=='pending_entry_and_stop_amended' for e in result['events']))

    def test_buy_sequence_uses_mirrored_levels(self):
        zone=Zone('BUY',155.2,155.4,self.t-timedelta(hours=2))
        liquidity=LiquidityReference(155.5,self.t-timedelta(hours=1))
        bars=[Bar(self.t+timedelta(minutes=i),155.5,155.7,155.35 if i==6 else 155.45,155.5) for i in range(15)]
        result=scan_lc1(zone,liquidity,bars,[self.candle(bars)],True)
        signal=result['signals'][0]
        self.assertEqual((signal['entry_level'],signal['stop_level']),(155.7,155.35))

    def test_missing_minutes_cannot_use_complete_future_replacement_ohlc(self):
        active=self.t+timedelta(minutes=15)
        signal={'side':'SELL','available_at':active.isoformat(),'signal_bar_start':self.t.isoformat(),
                'entry_level':155.2,'stop_level':155.7}
        last=Bar(active+timedelta(minutes=14),155.4,155.65,155.3,155.4)
        quarter=Bar(active,155.4,155.65,155.3,155.4)
        result=trace_pending_entry(signal,self.zone,[last],[quarter])
        self.assertEqual(result['status'],'review_required')
        self.assertFalse(any(e['event']=='pending_entry_and_stop_amended' for e in result['events']))


class InducementQualificationTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,12,tzinfo=timezone.utc)
        values=[(10,11,9,10),(10,12,9.8,11.5),(11,11.5,9.1,10),
                (10,10.5,8.9,9.5),(9.5,10,8.8,8.9)]
        self.bars=[Bar(self.t+timedelta(minutes=15*i),*v) for i,v in enumerate(values)]

    def qualify(self,bars):
        return qualify_inducement(bars,bars[1],bars[0],'SELL')

    def test_high_alone_is_not_qualified_without_opposite_break(self):
        result=self.qualify(self.bars[:3])
        self.assertEqual(result['status'],'awaiting_qualifying_break')
        self.assertIsNone(result['liquidity'])

    def test_wick_qualifies_before_a_later_close(self):
        result=self.qualify(self.bars)
        self.assertEqual(result['status'],'qualified')
        self.assertEqual(result['confirmation_quality'],'wick_only')
        self.assertEqual(result['liquidity'].level,12)
        self.assertEqual(result['liquidity'].available_at,self.t+timedelta(hours=1))
        self.assertEqual(result,self.qualify(self.bars[:4]))

    def test_close_adds_quality_without_becoming_an_extra_filter(self):
        bars=self.bars[:4];b=bars[-1]
        bars[-1]=Bar(b.timestamp,b.open,b.high,b.low,8.95)
        result=self.qualify(bars)
        self.assertEqual(result['status'],'qualified')
        self.assertEqual(result['confirmation_quality'],'close_confirmed')

    def test_buy_low_qualifies_on_prior_high_break(self):
        bars=[Bar(b.timestamp,22-b.open,22-b.low,22-b.high,22-b.close) for b in self.bars]
        result=qualify_inducement(bars,bars[1],bars[0],'BUY')
        self.assertEqual(result['status'],'qualified')
        self.assertEqual(result['liquidity'].level,10)
        self.assertEqual(result['confirmation_quality'],'wick_only')

    def test_future_prior_reference_cannot_qualify_origin(self):
        with self.assertRaises(ValueError):
            qualify_inducement(self.bars,self.bars[1],self.bars[2],'SELL')

    def test_origin_revisit_with_break_is_not_assumed_in_favorable_order(self):
        bars=self.bars[:4];b=bars[-1]
        bars[-1]=Bar(b.timestamp,b.open,12.1,b.low,b.close)
        result=self.qualify(bars)
        self.assertEqual(result['status'],'review_required')
        self.assertIsNone(result['liquidity'])

    def test_break_inside_origin_is_not_silently_deferred_to_later_bar(self):
        bars=self.bars[:];b=bars[1]
        bars[1]=Bar(b.timestamp,b.open,b.high,8.5,b.close)
        result=self.qualify(bars)
        self.assertEqual(result['status'],'review_required')
        self.assertEqual(result['reason'],'origin_contains_break_requires_intrabar_review')
        self.assertIsNone(result['liquidity'])

    def test_level_broken_before_origin_is_not_certified_as_a_new_break(self):
        prior=self.bars[0]
        between=Bar(self.t+timedelta(minutes=15),10,10.5,8.8,10)
        origin=Bar(self.t+timedelta(minutes=30),10,12,9.8,11.5)
        result=qualify_inducement([prior,between,origin,self.bars[3]],origin,prior,'SELL')
        self.assertEqual(result['status'],'review_required')
        self.assertEqual(result['reason'],'prior_level_already_crossed_before_origin')
        self.assertIsNone(result['liquidity'])


if __name__=='__main__':
    unittest.main()
