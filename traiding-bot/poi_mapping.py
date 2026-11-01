"""HTF POI origin candidates from a supplied structure reference/window.

Origin candles are discovered, not supplied. Structural scale/window selection
remains conditional. This does not assign phase, probability grades or orders.
"""

from datetime import datetime, timedelta
import math

from fractal_candidates import detect_candidates


def _validate(bars, interval):
    previous=None
    for b in bars:
        if b.timestamp.tzinfo is None:
            raise ValueError('Timezone-aware candles required')
        if previous is not None and b.timestamp<previous+interval:
            raise ValueError('Chronological nonoverlapping candles required')
        if not all(math.isfinite(v) and v>0 for v in (b.open,b.high,b.low,b.close)):
            raise ValueError('Positive finite OHLC required')
        if not b.low<=min(b.open,b.close)<=max(b.open,b.close)<=b.high:
            raise ValueError('Inconsistent OHLC')
        previous=b.timestamp


def _freshness(origin, known_at, side, quarters, interval):
    """Explicit M15 closed-departure convention, pending chart validation.

    Initial overlap while the move forms is not automatically a retest. After
    a close outside the near edge, any later overlap is a return. We do not
    claim to resolve an exit/retest inside one M15 candle from OHLC alone.
    """
    start=origin.timestamp+interval
    observed=[b for b in quarters if start<=b.timestamp<known_at]
    expected=[];cursor=start
    while cursor<known_at:
        expected.append(cursor);cursor+=timedelta(minutes=15)
    gap=[b.timestamp for b in observed]!=expected
    departure=None;return_at=None
    for b in observed:
        failed=b.low<origin.low if side=='BUY' else b.high>origin.high
        if failed:
            return {'status':'invalid_before_confirmation','observed_at':(b.timestamp+timedelta(minutes=15)).isoformat(),'quote_gap':gap}
        overlap=b.low<=origin.high and b.high>=origin.low
        if departure is not None and overlap and return_at is None:
            return_at=b.timestamp+timedelta(minutes=15)
        outside=b.close>origin.high if side=='BUY' else b.close<origin.low
        if departure is None and outside:departure=b.timestamp+timedelta(minutes=15)
    status=('quote_coverage_requires_review' if gap else
            'mitigated_before_confirmation' if return_at else
            'observed_unreturned_after_departure' if departure else
            'departure_not_established')
    return {'status':status,'departure_known_at':departure.isoformat() if departure else None,
            'return_known_at':return_at.isoformat() if return_at else None,
            'quote_gap':gap,'convention':'M15 close establishes departure; subsequent wick overlap is return; intrabar formation not resolved'}


def map_poi_candidates(context, quarters, reference, timeframe_minutes=60, leg_start=None):
    if timeframe_minutes not in (60,240):
        raise ValueError('POI context mapping is 1H/4H only')
    if reference.scale not in ('internal','swing'):
        raise ValueError('Supplied internal/swing close-break reference required')
    interval=timedelta(minutes=timeframe_minutes)
    _validate(context,interval);_validate(quarters,timedelta(minutes=15))
    start=reference.known_at if leg_start is None else leg_start
    if start.tzinfo is None or start<reference.known_at:
        raise ValueError('Mapping window must start after reference availability')
    bullish=reference.direction=='BUY'
    confirming=next((b for b in context if b.timestamp>=start and
                     (b.close>reference.price if bullish else b.close<reference.price)),None)
    scope='Discovered HTF origins conditional on supplied structure level/scale/window; no automatic hierarchy, phase, active-zone admission or trades'
    if confirming is None:
        return {'status':'awaiting_close_break','candidates':[],'scope':scope}
    known=confirming.timestamp+interval
    origins=[b for b in context if start<=b.timestamp<confirming.timestamp]
    if not origins:return {'status':'no_pre_break_origin','candidates':[],'scope':scope}
    history=[b for b in context if b.timestamp+interval<=known]
    patterns=detect_candidates(history,timeframe_minutes)
    available=[p for p in patterns if not p['requires_ordering_review'] and
               datetime.fromisoformat(p['available_at'])<=known]
    extreme=(min(b.low for b in origins) if bullish else max(b.high for b in origins))
    results=[]
    for origin in origins:
        price=origin.low if bullish else origin.high
        is_extreme=price==extreme
        supports=[p for p in available if p['confirmation_direction']==reference.direction and
                  origin.timestamp.isoformat() in p['reference_candle_starts']]
        if not is_extreme and not supports:continue
        sweeps=[]
        for p in available:
            if p['confirmation_direction']!=reference.direction:continue
            point_known=datetime.fromisoformat(p['available_at'])
            if point_known>origin.timestamp:continue
            point=p['reference_price']
            swept=origin.low<point if bullish else origin.high>point
            if not swept:continue
            intervening=[b for b in history if point_known<=b.timestamp<origin.timestamp]
            already=any((b.low<point if bullish else b.high>point) for b in intervening)
            if not already:
                sweeps.append({'price':point,'known_at':p['available_at'],
                               'reference_origins':p['reference_candle_starts'],
                               'evidence':'Source-candle range takes an earlier-known HTF reference; no intrabar ordering claimed'})
        fresh=_freshness(origin,known,reference.direction,quarters,interval)
        results.append({'side':reference.direction,'timeframe_minutes':timeframe_minutes,
                        'origin':origin.timestamp.isoformat(),'low':origin.low,'high':origin.high,
                        'available_at':known.isoformat(),'break_bar_start':confirming.timestamp.isoformat(),
                        'broken_level':reference.price,'confirmation_close':confirming.close,
                        'origin_pattern':'leg_extreme' if is_extreme else 'mid_leg',
                        'sweep_backed':bool(sweeps),'sweep_evidence':sweeps,
                        'local_break_supports':supports,'freshness':fresh,
                        'probability_grade':None,'requires_mapping_validation':True})
    # User's A/B example keeps the extreme origin A, not the immediately
    # following contained B supported only by a smaller local break. Keep
    # this rule narrow: it is not a ban on mid-leg or cross-timeframe nesting.
    by_origin={p['origin']:p for p in results}
    previous_bar={context[i].timestamp:context[i-1] for i in range(1,len(context))}
    retained=[];excluded=[]
    for candidate in results:
        before=previous_bar.get(datetime.fromisoformat(candidate['origin']))
        parent=by_origin.get(before.timestamp.isoformat()) if before else None
        same_origin=(parent is not None and parent['origin_pattern']=='leg_extreme'
                     and candidate['origin_pattern']=='mid_leg'
                     and not candidate['sweep_backed']
                     and before.timestamp+interval==datetime.fromisoformat(candidate['origin'])
                     and parent['low']<=candidate['low']<=candidate['high']<=parent['high'])
        if same_origin:
            excluded.append({**candidate,'reason':'adjacent_contained_candle_in_extreme_origin',
                             'retained_origin':parent['origin']})
        else:retained.append(candidate)
    return {'status':'candidates_found','known_at':known.isoformat(),
            'supplied_reference_price':reference.price,'supplied_reference_scale':reference.scale,
            'supplied_window_start':start.isoformat(),'candidates':retained,
            'excluded_candidates':excluded,'scope':scope}
