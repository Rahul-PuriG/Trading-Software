"""Causal M15 inducement candidates, separate from the HTF context map.

Enumerate prior candle levels and subsequent origin highs/lows that survive
until an opposite-level break. All qualifying alternatives are retained. This
does not identify POIs, rank candidates or authorize entries. Proximity is
quality information only; no maximum-distance eligibility filter applies.
"""

from dataclasses import dataclass, field
from datetime import timedelta
import math


@dataclass
class WaitingLevel:
    prior: object
    origins: list = field(default_factory=list)
    spans_quote_gap: bool = False


class InducementCandidateDetector:
    def __init__(self):
        self.interval = timedelta(minutes=15)
        self.waiting = {'BUY': [], 'SELL': []}
        self.previous = None

    def feed(self, candle):
        if (candle.timestamp.tzinfo is None or candle.timestamp.minute % 15
                or candle.timestamp.second or candle.timestamp.microsecond):
            raise ValueError('Aligned timezone-aware M15 candles required')
        if self.previous is not None and candle.timestamp < self.previous + self.interval:
            raise ValueError('M15 candles must be chronological and nonoverlapping')
        if not all(math.isfinite(v) and v > 0 for v in
                   (candle.open, candle.high, candle.low, candle.close)):
            raise ValueError('Positive finite M15 OHLC required')
        if not candle.low <= min(candle.open,candle.close) <= max(candle.open,candle.close) <= candle.high:
            raise ValueError('Inconsistent M15 OHLC')
        gap = self.previous is not None and candle.timestamp != self.previous + self.interval
        events = []
        for side in ('BUY', 'SELL'):
            remaining = []
            for level in self.waiting[side]:
                level.spans_quote_gap |= gap
                prior_price = level.prior.high if side == 'BUY' else level.prior.low
                crossed = candle.high > prior_price if side == 'BUY' else candle.low < prior_price
                if crossed:
                    for origin in level.origins:
                        price = origin.low if side == 'BUY' else origin.high
                        origin_also_crossed = candle.low < price if side == 'BUY' else candle.high > price
                        closed = candle.close > prior_price if side == 'BUY' else candle.close < prior_price
                        events.append({
                            'side': side, 'origin': origin.timestamp.isoformat(),
                            'source_timeframe_minutes':15,
                            'proximity_is_entry_filter':False,
                            'inducement_level': price,
                            'prior_reference': level.prior.timestamp.isoformat(),
                            'prior_reference_available_at': (level.prior.timestamp+self.interval).isoformat(),
                            'broken_level': prior_price,
                            'break_bar_start': candle.timestamp.isoformat(),
                            'available_at': (candle.timestamp+self.interval).isoformat(),
                            'status': 'review_required' if origin_also_crossed else 'qualified',
                            'reason': 'origin_crossed_with_qualifying_break' if origin_also_crossed else None,
                            'confirmation_quality': 'close_confirmed' if closed else 'wick_only',
                            'spans_quote_gap': level.spans_quote_gap,
                            'scope': 'Automatic M15 candidate only; proximity is quality only; pivot interpretation and trade eligibility unvalidated',
                        })
                    # A break inside the possible origin bar needs finer order
                    # evidence; do not quietly qualify that bar as its own origin.
                    events.append({
                        'side': side, 'origin': candle.timestamp.isoformat(),
                        'source_timeframe_minutes':15,
                        'proximity_is_entry_filter':False,
                        'inducement_level': candle.low if side == 'BUY' else candle.high,
                        'prior_reference': level.prior.timestamp.isoformat(),
                        'broken_level': prior_price,
                        'break_bar_start': candle.timestamp.isoformat(),
                        'available_at': (candle.timestamp+self.interval).isoformat(),
                        'status': 'review_required',
                        'reason': 'origin_contains_break_requires_intrabar_review',
                        'spans_quote_gap': level.spans_quote_gap,
                    })
                    continue
                # Origin extremes already crossed before this prior-level break
                # cannot be silently certified as untouched causal origins.
                level.origins = [o for o in level.origins if
                    (candle.low >= o.low if side == 'BUY' else candle.high <= o.high)]
                level.origins.append(candle)
                remaining.append(level)
            remaining.append(WaitingLevel(candle))
            self.waiting[side] = remaining
        self.previous = candle.timestamp
        return events


def detect_inducements(quarters):
    detector = InducementCandidateDetector()
    return [event for candle in quarters for event in detector.feed(candle)]
