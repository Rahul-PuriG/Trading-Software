from datetime import datetime,timedelta,timezone
import unittest

from backtest import Bar
from structure_evidence import StructureReference,evaluate_break


class StructureEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,29,12,tzinfo=timezone.utc)

    def reference(self,scale='fractal',direction='SELL'):
        return StructureReference(scale,direction,150,self.t)

    def test_fractal_wick_is_valid_without_close(self):
        candle=Bar(self.t,150.5,151,149.9,150.4)
        result=evaluate_break(self.reference(),candle)
        self.assertTrue(result['valid']);self.assertFalse(result['close_confirmed'])
        self.assertEqual(result['status'],'wick_valid')

    def test_internal_and_swing_need_close(self):
        wick=Bar(self.t,150.5,151,149.9,150.4)
        body=Bar(self.t+timedelta(minutes=15),150.4,150.5,149.5,149.8)
        for scale in ['internal','swing']:
            with self.subTest(scale=scale):
                ref=self.reference(scale)
                self.assertFalse(evaluate_break(ref,wick)['valid'])
                self.assertTrue(evaluate_break(ref,body)['valid'])

    def test_close_adds_confirmation_without_making_wick_invalid(self):
        wick=Bar(self.t,150.5,151,149.9,150.4)
        body=Bar(self.t+timedelta(minutes=15),150.4,150.5,149.5,149.8)
        self.assertTrue(evaluate_break(self.reference(),wick)['valid'])
        self.assertTrue(evaluate_break(self.reference(),body)['close_confirmed'])

    def test_bullish_fractal_break_uses_pullback_high(self):
        candle=Bar(self.t,149.8,150.2,149.5,149.9)
        self.assertEqual(evaluate_break(self.reference(direction='BUY'),candle)['status'],'wick_valid')

    def test_unavailable_reference_cannot_be_used_retroactively(self):
        candle=Bar(self.t-timedelta(minutes=15),150.5,151,149.9,150.4)
        self.assertEqual(evaluate_break(self.reference(),candle)['status'],'reference_not_available')


if __name__=='__main__':unittest.main()
