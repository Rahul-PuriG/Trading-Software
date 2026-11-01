"""Follow a supplied initial fractal direction through unambiguous CHoCH events.

Sequence resets use the confirmed A/B/C rule. The initial direction is explicit.
The preceding leg extreme becomes the opposite reference at a reversal; the
CHoCH candle starts the new A sequence. These two linking conventions still
need comparison with the user's chart annotations. Context structure is limited
to 1H/4H; M15 LC-1 structure is a separate, unimplemented qualification rule.
Ambiguous source candles halt unless complete minute evidence resolves the
confirmed outside-sequence policy. This module selects no POIs and sends no orders.
"""

from datetime import timedelta
import math

from fractal_candidates import FractalSequenceDetector
from structure_evidence import StructureReference, evaluate_break


def outside_sequence_order(candle, pattern, minutes, bar_minutes):
    """Observe the two crossings without inferring a path inside a minute.

    Evidence must cover the entire source candle and reproduce its OHLC. The
    proposed intervening reference is distinct from any already protected level.
    """
    end = candle.timestamp + timedelta(minutes=bar_minutes)
    inside = [b for b in minutes if candle.timestamp <= b.timestamp < end]
    expected = [candle.timestamp + timedelta(minutes=i) for i in range(bar_minutes)]
    if [b.timestamp for b in inside] != expected:
        return {'resolved': False, 'reason': 'incomplete_or_unordered_minute_evidence'}
    for b in inside:
        if (not all(math.isfinite(v) and v > 0 for v in (b.open,b.high,b.low,b.close))
                or not b.low <= min(b.open,b.close) <= max(b.open,b.close) <= b.high):
            return {'resolved': False, 'reason': 'invalid_minute_OHLC'}
    aggregate = (inside[0].open,max(b.high for b in inside),min(b.low for b in inside),inside[-1].close)
    if any(abs(a-b) > 1e-9 for a,b in zip(aggregate,(candle.open,candle.high,candle.low,candle.close))):
        return {'resolved': False, 'reason': 'minute_and_context_OHLC_mismatch'}
    bullish = pattern['confirmation_direction'] == 'BUY'
    level = pattern['anchor_break_level']
    reference = pattern['reference_price']
    first_a = next(i for i,b in enumerate(inside) if (b.high > level if bullish else b.low < level))
    first_reference = next(i for i,b in enumerate(inside) if
                           (b.low < reference if bullish else b.high > reference))
    evidence = {'resolved': first_a != first_reference,
                'directional_break_minute': inside[first_a].timestamp.isoformat(),
                'proposed_reference_break_minute': inside[first_reference].timestamp.isoformat()}
    if first_a == first_reference:
        return {**evidence, 'reason': 'both_first_crossings_in_same_minute'}
    if first_reference < first_a:
        return {**evidence, 'order': 'proposed_reference_first',
                'policy_result': 'no_fractal_break_from_this_new_point'}
    # The high/low that protects the reversal must be known before its crossing.
    prior = inside[:first_reference]
    turning = max(b.high for b in prior) if bullish else min(b.low for b in prior)
    crossing_bar = inside[first_reference]
    uncertain_turn = crossing_bar.high > turning if bullish else crossing_bar.low < turning
    returns = any((b.high > turning if bullish else b.low < turning)
                  for b in inside[first_reference+1:])
    if uncertain_turn or returns:
        return {**evidence, 'resolved': False,
                'reason': 'additional_turn_or_return_requires_finer_sequence_review'}
    return {**evidence, 'order': 'directional_break_first',
            'policy_result': 'fractal_choch', 'turning_price': turning}


class FractalStructureTracker:
    def __init__(self, direction, bar_minutes=60):
        if bar_minutes not in (60,240):
            raise ValueError('Context fractal structure uses 1H or 4H; M15 LC-1 rules are separate')
        self.sequence = FractalSequenceDetector(direction, bar_minutes)
        self.direction = direction
        self.interval = timedelta(minutes=bar_minutes)
        self.previous = None
        self.reference = None
        self.reference_origins = []
        self.turn_extreme = None
        self.turn_origins = []
        self.status = 'awaiting_first_reference'
        self.halted_reason = None
        self.leg_spans_quote_gap = False

    def _validate(self, candle):
        if self.halted_reason is not None:
            raise RuntimeError('Trace halted for ordering review; explicit reseeding required')
        if candle.timestamp.tzinfo is None:
            raise ValueError('Timezone-aware candles required')
        if self.previous is not None and candle.timestamp < self.previous + self.interval:
            raise ValueError('Candles must be chronological and nonoverlapping')
        prices = (candle.open, candle.high, candle.low, candle.close)
        if not all(math.isfinite(value) and value > 0 for value in prices):
            raise ValueError('Positive finite OHLC prices required')
        if not candle.low <= min(candle.open, candle.close) <= max(candle.open, candle.close) <= candle.high:
            raise ValueError('Inconsistent OHLC prices')
        if self.reference is not None and self.reference.known_at > candle.timestamp:
            raise ValueError('Fractal reference is not yet available')

    def _update_turn_extreme(self, candle):
        value = candle.high if self.direction == 'BUY' else candle.low
        better = self.turn_extreme is None or (
            value > self.turn_extreme if self.direction == 'BUY' else value < self.turn_extreme)
        if better:
            self.turn_extreme = value
            self.turn_origins = [candle.timestamp.isoformat()]
        elif value == self.turn_extreme:
            self.turn_origins.append(candle.timestamp.isoformat())

    def _halt(self, candle, reason, **details):
        self.status = 'review_required'
        self.halted_reason = reason
        self.previous = candle.timestamp
        event = {'event': 'fractal_ordering_review_required', 'reason': reason,
                 'known_at': (candle.timestamp + self.interval).isoformat(), **details}
        return self.snapshot([event])

    def feed(self, candle, minutes=None):
        self._validate(candle)
        end = candle.timestamp + self.interval
        if self.previous is not None:
            self.leg_spans_quote_gap |= candle.timestamp != self.previous + self.interval

        broken = evaluate_break(self.reference, candle) if self.reference else None
        if broken and broken['valid']:
            extends_turn = (candle.high > self.turn_extreme if self.direction == 'BUY'
                            else candle.low < self.turn_extreme)
            if extends_turn:
                return self._halt(candle, 'opposing_reference_and_new_leg_extreme_in_same_candle',
                                  broken_level=self.reference.price,
                                  prior_leg_extreme=self.turn_extreme)

            prior = self.direction
            broken_level = self.reference.price
            broken_origins = self.reference_origins[:]
            turning = self.turn_extreme
            turning_origins = self.turn_origins[:]
            self.direction = 'SELL' if prior == 'BUY' else 'BUY'
            # This opposite reference was not knowable at its old origin time.
            self.reference = StructureReference('fractal', prior, turning, end)
            self.reference_origins = turning_origins
            self.sequence = FractalSequenceDetector(
                self.direction, int(self.interval.total_seconds() // 60))
            self.sequence.feed(candle)
            self.turn_extreme = None
            self.turn_origins = []
            self._update_turn_extreme(candle)
            self.status = 'tracking'
            self.previous = candle.timestamp
            events = [{
                'event': 'fractal_choch', 'from_direction': prior,
                'direction': self.direction, 'broken_level': broken_level,
                'broken_reference_origins': broken_origins,
                'confirmation_quality': broken['confirmation_quality'],
                'known_at': end.isoformat(),
                'opposite_reference_price': turning,
                'opposite_reference_origins': turning_origins,
                'opposite_reference_known_at': end.isoformat(),
                'new_A_start': candle.timestamp.isoformat(),
                'spans_quote_gap': self.leg_spans_quote_gap,
                'linking_convention_requires_chart_validation': True,
            }]
            self.leg_spans_quote_gap = False
            return self.snapshot(events)

        patterns = self.sequence.feed(candle)
        if patterns and patterns[0]['requires_ordering_review']:
            pattern = patterns[0]
            if minutes is not None:
                evidence = outside_sequence_order(
                    candle, pattern, minutes, int(self.interval.total_seconds() // 60))
                if evidence['resolved']:
                    return self._apply_outside_sequence(candle, pattern, evidence)
                return self._halt(candle, evidence['reason'], pattern=pattern,
                                  minute_evidence=evidence)
            return self._halt(candle, 'breakout_also_crosses_proposed_new_reference',
                              pattern=patterns[0])
        self._update_turn_extreme(candle)
        events = []
        for pattern in patterns:
            opposite = 'SELL' if self.direction == 'BUY' else 'BUY'
            self.reference = StructureReference('fractal', opposite,
                                                pattern['reference_price'], end)
            self.reference_origins = pattern['reference_candle_starts'][:]
            self.status = 'tracking'
            events.append({'event': pattern['kind'], 'known_at': end.isoformat(),
                           'pattern': pattern})
        self.previous = candle.timestamp
        return self.snapshot(events)

    def _apply_outside_sequence(self, candle, pattern, evidence):
        end = candle.timestamp + self.interval
        if evidence['policy_result'] == 'no_fractal_break_from_this_new_point':
            # B was crossed before it could become the newly confirmed point.
            # Keep any previously confirmed protected reference separate.
            self._update_turn_extreme(candle)
            self.previous = candle.timestamp
            return self.snapshot([{
                'event': 'outside_sequence_no_fractal_break', 'known_at': end.isoformat(),
                'direction': self.direction, 'pattern': pattern,
                'minute_evidence': evidence,
            }])
        prior = self.direction
        self.direction = 'SELL' if prior == 'BUY' else 'BUY'
        turning = evidence['turning_price']
        self.reference = StructureReference('fractal', prior, turning, end)
        self.reference_origins = [candle.timestamp.isoformat()]
        self.sequence = FractalSequenceDetector(
            self.direction, int(self.interval.total_seconds() // 60))
        self.sequence.feed(candle)
        self.turn_extreme = None
        self.turn_origins = []
        self._update_turn_extreme(candle)
        self.status = 'tracking'
        self.previous = candle.timestamp
        event = {
            'event': 'fractal_choch', 'from_direction': prior, 'direction': self.direction,
            'broken_level': pattern['reference_price'],
            'broken_reference_origins': pattern['reference_candle_starts'],
            'confirmation_quality': 'close_confirmed' if (
                candle.close < pattern['reference_price'] if prior == 'BUY'
                else candle.close > pattern['reference_price']) else 'wick_only',
            'known_at': end.isoformat(),
            'opposite_reference_price': turning,
            'opposite_reference_origins': self.reference_origins[:],
            'opposite_reference_known_at': end.isoformat(),
            'new_A_start': candle.timestamp.isoformat(),
            'spans_quote_gap': self.leg_spans_quote_gap,
            'linking_convention_requires_chart_validation': True,
            'new_point_confirmed_then_broken_within_source_candle': True,
            'minute_evidence': evidence,
        }
        self.leg_spans_quote_gap = False
        return self.snapshot([event])

    def snapshot(self, events=None):
        return {
            'status': self.status, 'fractal_direction': self.direction,
            'opposing_reference': None if self.reference is None else {
                'price': self.reference.price,
                'break_direction': self.reference.direction,
                'known_at': self.reference.known_at.isoformat(),
                'origin_candle_starts': self.reference_origins[:],
            },
            'active_A_start': (self.sequence.anchor.candle.timestamp.isoformat()
                               if self.sequence.anchor else None),
            'halted_reason': self.halted_reason,
            'events': events or [],
            'context_timeframe_minutes': int(self.interval.total_seconds() // 60),
            'scope': '1H/4H context only; supplied initial direction; provisional reversal linking; M15 LC-1 rules separate',
        }


def trace_structure(candles, initial_direction, bar_minutes=60, internal=None, minutes=None):
    """Stop at the first ambiguity rather than inventing an intrabar path.

    Optional InternalPullbackTracker must use the same source candle duration;
    its initial direction/boundaries and availability remain caller inputs.
    """
    from internal_structure import FractalDirectionEvidence

    tracker = FractalStructureTracker(initial_direction, bar_minutes)
    if internal is not None and internal.interval != tracker.interval:
        raise ValueError('Fractal and internal traces must use the same source duration')
    events = []
    internal_events = []
    processed = 0
    for candle in candles:
        state = tracker.feed(candle, minutes=minutes)
        processed += 1
        events.extend(state['events'])
        if state['status'] == 'review_required':
            break
        if internal is not None:
            evidence = FractalDirectionEvidence(tracker.direction, candle.timestamp + tracker.interval)
            internal_events.extend(internal.update(candle, evidence)['events'])
    return {'processed_bars': processed, 'complete': tracker.halted_reason is None,
            'final_state': tracker.snapshot(), 'fractal_events': events,
            'internal_events': internal_events,
            'scope': 'Conditional 1H/4H context trace; M15 LC-1 qualification excluded; not a strategy backtest'}
