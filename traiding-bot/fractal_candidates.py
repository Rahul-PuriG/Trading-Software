"""Failure-then-break pullback patterns from completed candles.

FractalCandidateDetector retains nested possible A candles for diagnostics.
FractalSequenceDetector follows the confirmed advancing/freezing/resetting rule
for one supplied direction and starting candle. Neither assigns internal/swing
hierarchy, POIs, probability grades or trade entries.
"""

from dataclasses import dataclass,field
from datetime import timedelta
import math


@dataclass
class WaitingAnchor:
    side: str
    candle: object
    failures: int = 0
    extreme: float | None = None
    extreme_candles: list = field(default_factory=list)
    first_failure: object = None
    spans_quote_gap: bool = False

    def add_failure(self, candle):
        self.failures += 1
        self.first_failure = self.first_failure or candle.timestamp
        value = candle.low if self.side == 'BUY' else candle.high
        better = self.extreme is None or (value<self.extreme if self.side=='BUY' else value>self.extreme)
        if better:
            self.extreme=value
            self.extreme_candles=[candle.timestamp]
        elif value==self.extreme:
            self.extreme_candles.append(candle.timestamp)


def _confirmation_event(anchor,candle,interval):
    side=anchor.side
    level=anchor.candle.high if side=='BUY' else anchor.candle.low
    close_confirmed=candle.close>level if side=='BUY' else candle.close<level
    opposing_cross=candle.low<anchor.extreme if side=='BUY' else candle.high>anchor.extreme
    return {
        'kind':'fractal_low_candidate' if side=='BUY' else 'fractal_high_candidate',
        'confirmation_direction':side,
        'anchor_start':anchor.candle.timestamp.isoformat(),
        'anchor_break_level':level,
        'first_failed_candle':anchor.first_failure.isoformat(),
        'failed_candles':anchor.failures,
        'reference_price':anchor.extreme,
        'reference_candle_starts':[t.isoformat() for t in anchor.extreme_candles],
        'confirmation_candle_start':candle.timestamp.isoformat(),
        'available_at':(candle.timestamp+interval).isoformat(),
        'confirmation_candle_closed_beyond_A':close_confirmed,
        'confirmation_quality':'close_confirmed' if close_confirmed else 'wick_only',
        'reference_also_crossed_in_confirmation_candle':opposing_cross,
        'requires_ordering_review':opposing_cross,
        'spans_quote_gap':anchor.spans_quote_gap,
        'scope':'Candidate pattern only; no automatic hierarchy, POI or trade classification',
    }


class FractalCandidateDetector:
    def __init__(self,bar_minutes=15):
        if not isinstance(bar_minutes,int) or bar_minutes<=0:
            raise ValueError('Positive integer candle duration required')
        self.interval=timedelta(minutes=bar_minutes)
        self.waiting={'BUY':[],'SELL':[]}
        self.previous=None

    def feed(self,candle):
        if candle.timestamp.tzinfo is None:
            raise ValueError('Timezone-aware candles required')
        if self.previous is not None and candle.timestamp<=self.previous:
            raise ValueError('Candles must be chronological and unique')
        gap=self.previous is not None and candle.timestamp!=self.previous+self.interval
        events=[]
        for side in ('BUY','SELL'):
            remaining=[]
            for anchor in self.waiting[side]:
                anchor.spans_quote_gap |= gap
                level=anchor.candle.high if side=='BUY' else anchor.candle.low
                crossed=candle.high>level if side=='BUY' else candle.low<level
                if not crossed:
                    anchor.add_failure(candle)
                    remaining.append(anchor)
                    continue
                if anchor.failures:
                    # The diagram doesn't resolve an outside breakout candle that
                    # also trades through the proposed opposite extreme. Keep the
                    # pattern but flag ordering/reference validity for review.
                    events.append(_confirmation_event(anchor,candle,self.interval))
                # If the next candle immediately exceeds A without a failed
                # candle in between, there was no pullback to confirm.
            remaining.append(WaitingAnchor(side,candle))
            self.waiting[side]=remaining
        self.previous=candle.timestamp
        return events


def detect_candidates(candles,bar_minutes=15):
    detector=FractalCandidateDetector(bar_minutes)
    return [event for candle in candles for event in detector.feed(candle)]


class FractalSequenceDetector:
    """One directional sequence, initialized by its first supplied candle.

    Before a failure, advance A with each new directional extreme. After a
    failure, freeze A until its level breaks, emit the intervening opposite
    extreme and restart from C. Direction changes/reseeding belong to the caller.
    """

    def __init__(self,direction,bar_minutes=15):
        if direction not in ('BUY','SELL'):
            raise ValueError('BUY or SELL sequence direction required')
        if not isinstance(bar_minutes,int) or bar_minutes<=0:
            raise ValueError('Positive integer candle duration required')
        self.direction=direction
        self.interval=timedelta(minutes=bar_minutes)
        self.anchor=None
        self.previous=None

    def feed(self,candle):
        if candle.timestamp.tzinfo is None:
            raise ValueError('Timezone-aware candles required')
        if self.previous is not None and candle.timestamp<self.previous+self.interval:
            raise ValueError('Candles must be chronological and nonoverlapping')
        if not all(math.isfinite(value) and value>0 for value in
                   (candle.open,candle.high,candle.low,candle.close)):
            raise ValueError('Positive finite OHLC prices required')
        if not candle.low<=min(candle.open,candle.close)<=max(candle.open,candle.close)<=candle.high:
            raise ValueError('Inconsistent OHLC prices')
        events=[]
        if self.anchor is None:
            self.anchor=WaitingAnchor(self.direction,candle)
        else:
            self.anchor.spans_quote_gap |= candle.timestamp!=self.previous+self.interval
            level=self.anchor.candle.high if self.direction=='BUY' else self.anchor.candle.low
            crossed=candle.high>level if self.direction=='BUY' else candle.low<level
            if crossed:
                if self.anchor.failures:
                    event=_confirmation_event(self.anchor,candle,self.interval)
                    event['sequence_selected']=True
                    event['confirmed']=not event['requires_ordering_review']
                    if event['confirmed']:
                        event['kind']='fractal_low_confirmed' if self.direction=='BUY' else 'fractal_high_confirmed'
                    event['scope']='Directional sequence from supplied start; no automatic trend initialization, hierarchy or trade classification'
                    events.append(event)
                # C is the next A, even when no intervening failure was present.
                # Its range belongs to the new sequence, not the prior pullback.
                self.anchor=WaitingAnchor(self.direction,candle)
            else:
                self.anchor.add_failure(candle)
        self.previous=candle.timestamp
        return events


def detect_sequence(candles,direction,bar_minutes=15):
    detector=FractalSequenceDetector(direction,bar_minutes)
    return [event for candle in candles for event in detector.feed(candle)]
