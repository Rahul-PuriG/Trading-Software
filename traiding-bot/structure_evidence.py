"""Evaluate breaks of already identified structure references.

Does not select pullback pivots. Caller must supply a reference that was known
before the tested candle. Works on completed candles; it makes no claim about
the precise intrabar timestamp of a wick crossing.
"""

from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class StructureReference:
    scale: str
    direction: str
    price: float
    known_at: datetime

    def __post_init__(self):
        if self.scale not in ('fractal','internal','swing'):
            raise ValueError('Unknown structure scale')
        if self.direction not in ('BUY','SELL') or not math.isfinite(self.price) or self.price<=0:
            raise ValueError('Invalid break direction or reference price')
        if self.known_at.tzinfo is None:
            raise ValueError('Timezone-aware reference availability required')


def evaluate_break(reference, candle):
    if candle.timestamp<reference.known_at:
        return {'valid':False,'status':'reference_not_available','wick_crossed':False,'close_confirmed':False}
    if reference.direction=='BUY':
        wick=candle.high>reference.price
        body=candle.close>reference.price
    else:
        wick=candle.low<reference.price
        body=candle.close<reference.price
    valid=wick if reference.scale=='fractal' else body
    return {'valid':valid,'status':('close_confirmed' if body else
            'wick_valid' if wick and reference.scale=='fractal' else
            'close_required' if wick else 'unbroken'),
            'wick_crossed':wick,'close_confirmed':body,
            'confirmation_quality':('close_confirmed' if body else 'wick_only' if wick else 'none'),
            'scale':reference.scale,'direction':reference.direction,'reference_price':reference.price}
