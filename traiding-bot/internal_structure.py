"""Internal pullback state from already identified fractal-direction evidence.

Initial internal boundaries and controlling fractal changes are explicit inputs.
This does not select those inputs, assign swing phases or generate trade orders.
All updates use completed candles of the selected internal timeframe.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass(frozen=True)
class FractalDirectionEvidence:
    direction: str
    known_at: datetime

    def __post_init__(self):
        if self.direction not in ('BUY','SELL') or self.known_at.tzinfo is None:
            raise ValueError('Direction and timezone-aware evidence time required')


class InternalPullbackTracker:
    def __init__(self,direction,high,low,known_at,timeframe_minutes=60):
        if direction not in ('BUY','SELL') or not all(math.isfinite(v) for v in (high,low)) or not 0<low<high:
            raise ValueError('Valid direction and positive low < high required')
        if known_at.tzinfo is None or not isinstance(timeframe_minutes,int) or timeframe_minutes<=0:
            raise ValueError('Timezone-aware initialization and positive candle duration required')
        self.direction=direction;self.high=high;self.low=low
        self.known_at=known_at;self.interval=timedelta(minutes=timeframe_minutes)
        self.fractal_direction=direction;self.fractal_known_at=known_at
        self.previous=None;self.state='aligned'
        self.continuation_level=None;self.pullback_extreme=None
        self.pullback_origin=None;self.pullback_started_at=None
        self.reversal_extreme=high if direction=='BUY' else low

    def _depth(self):
        if self.pullback_extreme is None:return None
        width=(self.continuation_level-self.low if self.direction=='BUY'
               else self.high-self.continuation_level)
        if width<=0:return None
        return ((self.continuation_level-self.pullback_extreme) if self.direction=='BUY'
                else (self.pullback_extreme-self.continuation_level))/width

    def _clear_pullback(self):
        self.continuation_level=self.pullback_extreme=self.pullback_origin=self.pullback_started_at=None

    def update(self,candle,fractal=None):
        if candle.timestamp.tzinfo is None or candle.timestamp<self.known_at:
            raise ValueError('Candle precedes available initial structure')
        if self.previous is not None and candle.timestamp<self.previous+self.interval:
            raise ValueError('Candles must be chronological and nonoverlapping')
        prices=(candle.open,candle.high,candle.low,candle.close)
        if not all(math.isfinite(value) and value>0 for value in prices):
            raise ValueError('Positive finite OHLC prices required')
        if not candle.low<=min(candle.open,candle.close)<=max(candle.open,candle.close)<=candle.high:
            raise ValueError('Inconsistent OHLC prices')
        end=candle.timestamp+self.interval
        if fractal is not None:
            if fractal.known_at>end:raise ValueError('Fractal evidence is from the future')
            if fractal.known_at<self.fractal_known_at:raise ValueError('Stale fractal direction evidence')
        self.previous=candle.timestamp
        if fractal is not None:
            self.fractal_direction=fractal.direction;self.fractal_known_at=fractal.known_at
        bullish=self.direction=='BUY'
        self.reversal_extreme=(max(self.reversal_extreme,candle.high) if bullish
                               else min(self.reversal_extreme,candle.low))
        events=[]
        reversed_by_close=candle.close<self.low if bullish else candle.close>self.high
        if reversed_by_close:
            prior=self.direction
            boundary=self.low if bullish else self.high
            turning=self.reversal_extreme
            self.direction='SELL' if bullish else 'BUY'
            if bullish:
                self.high=turning;self.low=min(candle.low,self.pullback_extreme or candle.low)
            else:
                self.low=turning;self.high=max(candle.high,self.pullback_extreme or candle.high)
            self.state='aligned' if self.fractal_direction==self.direction else 'fractal_alignment_unresolved'
            self.reversal_extreme=self.low if self.direction=='SELL' else self.high
            self._clear_pullback()
            events.append({'event':'internal_direction_reversed','from_direction':prior,
                'direction':self.direction,'broken_level':boundary,'close':candle.close,
                'confirmed_turning_point':turning,'known_at':end.isoformat()})
            return self.snapshot(events)

        opposing=self.fractal_direction!=self.direction
        if self.pullback_started_at is None and opposing:
            self.continuation_level=max(self.high,candle.high) if bullish else min(self.low,candle.low)
            self.pullback_extreme=candle.low if bullish else candle.high
            self.pullback_origin=candle.timestamp;self.pullback_started_at=end
            self.state='pullback'
            events.append({'event':'internal_pullback_started','direction':self.direction,
                           'continuation_level':self.continuation_level,'known_at':end.isoformat()})
        elif self.pullback_started_at is not None:
            value=candle.low if bullish else candle.high
            better=value<self.pullback_extreme if bullish else value>self.pullback_extreme
            if better:self.pullback_extreme=value;self.pullback_origin=candle.timestamp
            if opposing:
                self.state='pullback'
            else:
                if self.state!='alignment_returned':
                    events.append({'event':'fractal_alignment_returned','candidate_internal_pivot':self.pullback_extreme,
                                   'known_at':end.isoformat()})
                self.state='alignment_returned'
            continuation=candle.close>self.continuation_level if bullish else candle.close<self.continuation_level
            if continuation and not opposing:
                depth=self._depth();pivot=self.pullback_extreme
                events.append({'event':'internal_pullback_low_confirmed' if bullish else 'internal_pullback_high_confirmed',
                    'pivot_price':pivot,'pivot_origin':self.pullback_origin.isoformat(),
                    'prior_internal_level':self.continuation_level,'confirmation_close':candle.close,
                    'retracement_fraction':depth,'depth_in_preferred_36_50_band':depth is not None and .36<=depth<=.5,
                    'known_at':end.isoformat()})
                if bullish:self.low=pivot;self.high=candle.high
                else:self.high=pivot;self.low=candle.low
                self.state='aligned';self.reversal_extreme=self.high if bullish else self.low
                self._clear_pullback()
            elif continuation:
                events.append({'event':'continuation_close_without_fractal_alignment_requires_review',
                               'known_at':end.isoformat()})
        else:
            if bullish:self.high=max(self.high,candle.high)
            else:self.low=min(self.low,candle.low)
        return self.snapshot(events)

    def snapshot(self,events=None):
        depth=self._depth()
        return {'internal_direction':self.direction,'fractal_direction':self.fractal_direction,
            'state':self.state,'confirmed_internal_high':self.high,'confirmed_internal_low':self.low,
            'candidate_internal_pivot':self.pullback_extreme,'continuation_level':self.continuation_level,
            'retracement_fraction':depth,'depth_is_filter':False,'events':events or [],
            'scope':'Conditional internal-state tracking; initial boundaries and fractal-direction evidence supplied separately'}
