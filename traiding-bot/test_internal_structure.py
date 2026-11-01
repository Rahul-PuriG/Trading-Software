from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from internal_structure import InternalPullbackTracker,FractalDirectionEvidence
from structure_evidence import StructureReference,evaluate_break


class InternalStructureTests(unittest.TestCase):
    def setUp(self):self.t=datetime(2025,1,29,12,tzinfo=timezone.utc)

    def tracker(self,side='BUY'):
        return InternalPullbackTracker(side,151,149,self.t)

    def evidence(self,direction,bar):
        return FractalDirectionEvidence(direction,bar.timestamp+timedelta(hours=1))

    def test_fractal_return_does_not_confirm_internal_pivot_before_BOS(self):
        tr=self.tracker()
        first=Bar(self.t,150.8,150.9,150.2,150.4)
        tr.update(first,self.evidence('SELL',first))
        back=Bar(self.t+timedelta(hours=1),150.4,150.95,150.3,150.8)
        state=tr.update(back,self.evidence('BUY',back))
        self.assertEqual(state['state'],'alignment_returned')
        self.assertEqual(state['candidate_internal_pivot'],150.2)
        self.assertEqual(state['confirmed_internal_low'],149)
        self.assertFalse(any(e['event']=='internal_pullback_low_confirmed' for e in state['events']))
        bos=Bar(self.t+timedelta(hours=2),150.8,151.3,150.6,151.1)
        result=tr.update(bos)
        self.assertEqual(result['confirmed_internal_low'],150.2)
        confirmed=next(e for e in result['events'] if e['event']=='internal_pullback_low_confirmed')
        self.assertEqual(confirmed['known_at'],(bos.timestamp+timedelta(hours=1)).isoformat())

    def test_internal_BOS_wick_does_not_confirm(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,150.2,150.4)
        tr.update(b,self.evidence('SELL',b))
        wick=Bar(self.t+timedelta(hours=1),150.4,151.2,150.3,150.9)
        state=tr.update(wick,self.evidence('BUY',wick))
        self.assertEqual(state['confirmed_internal_low'],149)
        self.assertEqual(state['state'],'alignment_returned')

    def test_bearish_mirror_confirms_pullback_high_after_close(self):
        tr=self.tracker('SELL');b=Bar(self.t,149.5,149.8,149.3,149.6)
        tr.update(b,self.evidence('BUY',b))
        back=Bar(self.t+timedelta(hours=1),149.6,149.7,149.1,149.2)
        tr.update(back,self.evidence('SELL',back))
        bos=Bar(self.t+timedelta(hours=2),149.2,149.4,148.7,148.9)
        state=tr.update(bos)
        self.assertEqual(state['confirmed_internal_high'],149.8)
        self.assertEqual(state['state'],'aligned')

    def test_opposing_fractal_change_alone_does_not_reverse_internal(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,148.9,149.5)
        result=tr.update(b,self.evidence('SELL',b))
        self.assertEqual(result['internal_direction'],'BUY')
        self.assertEqual(result['state'],'pullback')
        nextbar=Bar(self.t+timedelta(hours=1),149.5,149.7,148.5,148.8)
        result=tr.update(nextbar)
        self.assertEqual(result['internal_direction'],'SELL')
        self.assertEqual(result['events'][0]['event'],'internal_direction_reversed')

    def test_depth_preference_is_not_a_hard_filter(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,150.8,150.85)
        tr.update(b,self.evidence('SELL',b))
        bos=Bar(self.t+timedelta(hours=1),150.85,151.3,150.85,151.2)
        result=tr.update(bos,self.evidence('BUY',bos))
        event=next(e for e in result['events'] if e['event']=='internal_pullback_low_confirmed')
        self.assertFalse(event['depth_in_preferred_36_50_band'])
        self.assertEqual(result['confirmed_internal_low'],150.8)

    def test_future_fractal_evidence_rejected(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,150.2,150.4)
        with self.assertRaises(ValueError):
            tr.update(b,FractalDirectionEvidence('SELL',self.t+timedelta(hours=2)))

    def test_close_at_internal_level_does_not_confirm(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,150.2,150.4)
        tr.update(b,self.evidence('SELL',b))
        touch=Bar(self.t+timedelta(hours=1),150.4,151.2,150.3,151)
        state=tr.update(touch,self.evidence('BUY',touch))
        self.assertEqual(state['confirmed_internal_low'],149)
        self.assertEqual(state['state'],'alignment_returned')

    def test_bad_prices_are_rejected_without_advancing_state(self):
        tr=self.tracker();before=tr.snapshot()
        for prices in ((150.8,150.9,150.85,150.88),
                       (150.8,float('nan'),150.2,150.4),
                       (150.8,150.9,0,150.4)):
            with self.subTest(prices=prices), self.assertRaises(ValueError):
                tr.update(Bar(self.t,*prices))
            self.assertEqual(tr.snapshot(),before)
            self.assertIsNone(tr.previous)
        valid=Bar(self.t,150.8,150.9,150.2,150.4)
        self.assertEqual(tr.update(valid,self.evidence('SELL',valid))['state'],'pullback')

    def test_overlapping_candles_cannot_advance_confirmation(self):
        tr=self.tracker();b=Bar(self.t,150.8,150.9,150.2,150.4)
        tr.update(b,self.evidence('SELL',b))
        overlap=Bar(self.t+timedelta(minutes=30),150.4,151.3,150.3,151.2)
        with self.assertRaises(ValueError):tr.update(overlap)
        self.assertEqual(tr.snapshot()['confirmed_internal_low'],149)

    def test_newer_fractal_low_break_starts_pullback_while_older_low_holds(self):
        tr=InternalPullbackTracker('BUY',151,149.5,self.t)
        older=StructureReference('fractal','SELL',150,self.t)
        newer=StructureReference('fractal','SELL',150.3,self.t)
        candle=Bar(self.t,150.8,150.85,150.2,150.6)
        self.assertFalse(evaluate_break(older,candle)['valid'])
        broken=evaluate_break(newer,candle)
        self.assertTrue(broken['valid'])
        self.assertFalse(broken['close_confirmed'])
        state=tr.update(candle,self.evidence(newer.direction,candle))
        self.assertEqual(state['state'],'pullback')
        self.assertEqual(state['internal_direction'],'BUY')
        self.assertEqual(state['confirmed_internal_low'],149.5)
        self.assertEqual(state['events'][0]['event'],'internal_pullback_started')

    def test_newer_fractal_high_break_starts_bearish_internal_pullback(self):
        tr=InternalPullbackTracker('SELL',151.5,149,self.t)
        older=StructureReference('fractal','BUY',150,self.t)
        newer=StructureReference('fractal','BUY',149.7,self.t)
        candle=Bar(self.t,149.2,149.8,149.15,149.4)
        self.assertFalse(evaluate_break(older,candle)['valid'])
        broken=evaluate_break(newer,candle)
        self.assertTrue(broken['valid'])
        self.assertFalse(broken['close_confirmed'])
        state=tr.update(candle,self.evidence(newer.direction,candle))
        self.assertEqual(state['state'],'pullback')
        self.assertEqual(state['internal_direction'],'SELL')
        self.assertEqual(state['confirmed_internal_high'],151.5)
        self.assertEqual(state['events'][0]['event'],'internal_pullback_started')


if __name__=='__main__':unittest.main()
