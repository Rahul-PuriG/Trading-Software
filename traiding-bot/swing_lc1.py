"""Causal LC-1 sequence checks using annotated POI and liquidity references.

This is not an automatic structure/phase/POI selector. It emits setup events,
never broker orders. Unspecified late-mitigation cases are flagged for review.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from backtest import Bar


@dataclass(frozen=True)
class Zone:
    side: str
    low: float
    high: float
    available_at: datetime

    def __post_init__(self):
        if self.side not in ("BUY", "SELL") or not 0 < self.low < self.high:
            raise ValueError("Expected BUY/SELL and positive low < high")
        if self.available_at.tzinfo is None:
            raise ValueError("Timezone-aware zone confirmation required")


@dataclass(frozen=True)
class LiquidityReference:
    level: float
    available_at: datetime
    source_timeframe_minutes: int = 15

    def __post_init__(self):
        if not math.isfinite(self.level) or self.level <= 0 or self.available_at.tzinfo is None:
            raise ValueError("Positive liquidity level and timezone-aware availability required")
        if self.source_timeframe_minutes != 15:
            raise ValueError('LC-1 inducement is identified on the M15 entry timeframe only')


def qualify_inducement(quarters, origin, prior, side):
    """Qualify a selected M15 high/low by its subsequent opposite-level break.

    SELL: origin high must lead to price below the prior M15 low; BUY mirrors it.
    A wick suffices and a close adds quality. The source candle must be complete
    before this OHLC-only implementation makes its evidence available. Selecting
    Origin/prior selection remains a caller input. POI proximity is quality
    information, not an admission filter. Formation in a
    pullback or a newer inducement to the right does not disqualify the point.
    There is no left-leg-only or no-PBID filter.
    """
    if side not in ('BUY','SELL'):
        raise ValueError('BUY or SELL inducement direction required')
    interval=timedelta(minutes=15)
    previous=None;lookup={}
    for b in quarters:
        if (b.timestamp.tzinfo is None or b.timestamp.minute%15 or
                b.timestamp.second or b.timestamp.microsecond):
            raise ValueError('Aligned timezone-aware M15 candles required')
        if previous is not None and b.timestamp<previous+interval:
            raise ValueError('M15 candles must be chronological and nonoverlapping')
        if not all(math.isfinite(v) and v>0 for v in (b.open,b.high,b.low,b.close)):
            raise ValueError('Positive finite M15 OHLC required')
        if not b.low<=min(b.open,b.close)<=max(b.open,b.close)<=b.high:
            raise ValueError('Inconsistent M15 OHLC')
        lookup[b.timestamp]=b;previous=b.timestamp
    if lookup.get(origin.timestamp)!=origin or lookup.get(prior.timestamp)!=prior:
        raise ValueError('Origin and prior reference must be candles from the M15 input')
    if prior.timestamp+interval>origin.timestamp:
        raise ValueError('Prior M15 level must be available before the inducement origin')
    level=origin.high if side=='SELL' else origin.low
    broken_level=prior.low if side=='SELL' else prior.high
    result={'side':side,'origin':origin.timestamp.isoformat(),
            'inducement_level':level,'prior_reference':prior.timestamp.isoformat(),
            'prior_reference_available_at':(prior.timestamp+interval).isoformat(),
            'broken_level':broken_level,'liquidity':None,
            'scope':'Selected M15 origin/prior only; no proximity, left-leg-only or no-PBID admission filter'}
    for b in quarters:
        if not prior.timestamp+interval<=b.timestamp<=origin.timestamp:continue
        already_crossed=b.low<broken_level if side=='SELL' else b.high>broken_level
        if already_crossed:
            return {**result,'status':'review_required',
                    'reason':('origin_contains_break_requires_intrabar_review'
                              if b.timestamp==origin.timestamp else
                              'prior_level_already_crossed_before_origin'),
                    'break_bar_start':b.timestamp.isoformat()}
    origin_crossed=False;gap=False;previous=origin.timestamp
    for b in quarters:
        if b.timestamp<origin.timestamp+interval:continue
        gap |= b.timestamp!=previous+interval
        previous=b.timestamp
        crossed=(b.high>level if side=='SELL' else b.low<level)
        wick=(b.low<broken_level if side=='SELL' else b.high>broken_level)
        close=(b.close<broken_level if side=='SELL' else b.close>broken_level)
        if wick:
            if origin_crossed or crossed:
                return {**result,'status':'review_required',
                        'reason':'origin_crossed_before_or_with_qualifying_break',
                        'break_bar_start':b.timestamp.isoformat(),
                        'spans_quote_gap':gap}
            available=b.timestamp+interval
            return {**result,'status':'qualified','break_bar_start':b.timestamp.isoformat(),
                    'available_at':available.isoformat(),'spans_quote_gap':gap,
                    'confirmation_quality':'close_confirmed' if close else 'wick_only',
                    'liquidity':LiquidityReference(level,available)}
        origin_crossed |= crossed
    return {**result,'status':'awaiting_qualifying_break','spans_quote_gap':gap}


def hourly_bars(quarters):
    """Only full UTC-hour groups; no fabricated candles through quote gaps."""
    groups = {}
    for b in quarters:
        key = b.timestamp.replace(minute=0, second=0, microsecond=0)
        groups.setdefault(key, []).append(b)
    result = []
    for start, group in sorted(groups.items()):
        group.sort(key=lambda b: b.timestamp)
        if [b.timestamp for b in group] != [start+timedelta(minutes=15*i) for i in range(4)]:
            continue
        result.append(Bar(start,group[0].open,max(b.high for b in group),
                          min(b.low for b in group),group[-1].close))
    return result


def zone_after_break(hours, origin, level, side):
    """Confirm an annotated origin candle only after a close through an annotated level."""
    if side not in ("BUY", "SELL") or level <= 0:
        raise ValueError("Invalid side or structure level")
    for b in hours:
        if b.timestamp < origin.timestamp + timedelta(hours=1):
            continue
        crossed = b.close > level if side == "BUY" else b.close < level
        if crossed:
            return Zone(side,origin.low,origin.high,b.timestamp+timedelta(hours=1))
    return None


def scan_lc1(zone, liquidity, minutes, quarters, context_approved):
    """Find a sweep/mitigation/closed-candle sequence; context is an annotated input.

    Minute OHLC observations become usable at minute end. The reference level
    availability must reflect its real qualification time, not just its old pivot.
    """
    events, signals = [], []
    lookup = {b.timestamp:b for b in quarters}
    seen = {}
    touched = None
    candidate = None
    swept = False
    closed_candidate = None
    valid = True
    setup_invalid = False
    if not context_approved:
        return {"zone_valid":None,"status":"context_not_approved","events":[],"signals":[]}
    for minute in minutes:
        observed_at = minute.timestamp + timedelta(minutes=1)
        quarter = minute.timestamp.replace(minute=minute.timestamp.minute//15*15,second=0,microsecond=0)
        seen.setdefault(quarter, []).append(minute)
        if minute.timestamp < zone.available_at:
            continue
        breached = minute.low < zone.low if zone.side == "BUY" else minute.high > zone.high
        if breached:
            valid = False
            events.append({"event":"poi_invalidated","minute":minute.timestamp.isoformat(),
                           "known_at":observed_at.isoformat()})
            break
        overlap = minute.low <= zone.high and minute.high >= zone.low
        invalidation = False
        if closed_candidate is not None and touched is None:
            if quarter > closed_candidate.timestamp+timedelta(minutes=15):
                events.append({"event":"pre_touch_validity_after_next_candle_requires_review",
                               "known_at":minute.timestamp.isoformat()})
                break
            invalidation = (minute.high > closed_candidate.high if zone.side == "BUY"
                            else minute.low < closed_candidate.low)
        if invalidation:
            setup_invalid = True
            events.append({"event":"early_invalidation" if not overlap else "ambiguous_touch_and_early_invalidation",
                           "minute":minute.timestamp.isoformat(),"known_at":observed_at.isoformat()})
            # Reject this sequence conservatively; zone itself remains valid.
            closed_candidate = None
        if overlap and touched is None:
            touched = minute.timestamp
            events.append({"event":"poi_mitigated","minute":minute.timestamp.isoformat(),
                           "known_at":observed_at.isoformat()})
        if not swept and minute.timestamp >= liquidity.available_at:
            crossed = minute.low < liquidity.level if zone.side == "BUY" else minute.high > liquidity.level
            if crossed:
                swept = True
                candidate = quarter
                events.append({"event":"liquidity_swept","minute":minute.timestamp.isoformat(),
                               "known_at":observed_at.isoformat()})
        if candidate is not None and observed_at == candidate+timedelta(minutes=15):
            candle = lookup.get(candidate)
            group = seen[candidate]
            if candle is None or [b.timestamp for b in group] != [candidate+timedelta(minutes=i) for i in range(15)]:
                events.append({"event":"incomplete_liquidation_candle","known_at":observed_at.isoformat()})
                break
            actual = (group[0].open,max(b.high for b in group),min(b.low for b in group),group[-1].close)
            if any(abs(a-b)>1e-8 for a,b in zip(actual,(candle.open,candle.high,candle.low,candle.close))):
                raise ValueError("Minute/quarter OHLC mismatch")
            if touched is not None and not setup_invalid:
                if not(candle.low<=zone.high and candle.high>=zone.low):
                    events.append({'event':'liquidation_candle_outside_poi_requires_review',
                                   'known_at':observed_at.isoformat()})
                    break
                signals.append({"side":zone.side,"signal_bar_start":candidate.isoformat(),
                    "available_at":observed_at.isoformat(),
                    "entry_level":candle.high if zone.side=="BUY" else candle.low,
                    "stop_level":candle.low if zone.side=="BUY" else candle.high,
                    "inducement_timeframe_minutes":liquidity.source_timeframe_minutes,
                    "inducement_distance_to_poi_pips":round(max(
                        zone.low-liquidity.level,liquidity.level-zone.high,0)/.01,8),
                    "proximity_is_entry_filter":False,
                    "scope":"Annotated context/zone/liquidity inputs; initial LC-1 sequence only"})
                events.append({"event":"pending_entry_eligible","known_at":observed_at.isoformat()})
                break
            closed_candidate = candle
            candidate = None
        elif touched is not None and closed_candidate is not None and not setup_invalid:
            # The diagrams allow liquidation before mitigation. Selecting which
            # candle to use for an entry in this later-touch case is not yet agreed.
            events.append({"event":"later_mitigation_requires_entry_candle_review",
                           "known_at":observed_at.isoformat()})
            break
    return {"zone_valid":valid,"setup_early_invalidated":setup_invalid,
            "status":"signal_found" if signals else "no_signal_or_review_required",
            "events":events,"signals":signals}


def trace_pending_entry(signal, zone, minutes, quarters, spread_pips=1.0, slippage_pips=.1):
    """Trace entry triggers and closed-candle amendments before the first fill.

    Replacements require a candle overlapping the valid POI. A replacement candle
    wholly outside the POI is flagged, since its treatment is not yet confirmed.
    This function emits events only; no account or actual orders are modified.
    """
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("Negative spread/slippage")
    side=signal['side'];active=datetime.fromisoformat(signal['available_at'])
    if side!=zone.side:raise ValueError("Signal and zone directions differ")
    current=dict(signal);events=[];lookup={b.timestamp:b for b in quarters};seen={}
    half=spread_pips*.01/2;slip=slippage_pips*.01
    for b in minutes:
        if b.timestamp<active:continue
        quarter_start=b.timestamp.replace(minute=b.timestamp.minute//15*15,second=0,microsecond=0)
        seen.setdefault(quarter_start,[]).append(b)
        breached=b.low<zone.low if side=='BUY' else b.high>zone.high
        trigger=(b.high+half>=current['entry_level']) if side=='BUY' else (b.low-half<=current['entry_level'])
        if breached:
            events.append({'event':'pending_cancelled_poi_invalid','minute':b.timestamp.isoformat(),
                           'entry_also_possible_in_same_minute':bool(trigger)})
            return {'status':'cancelled_or_ambiguous','events':events,'last_signal':current}
        if trigger:
            executable_open=b.open+half if side=='BUY' else b.open-half
            fill=(max(executable_open,current['entry_level'])+slip if side=='BUY'
                  else min(executable_open,current['entry_level'])-slip)
            events.append({'event':'entry_triggered','minute':b.timestamp.isoformat(),'fill_price':fill})
            return {'status':'filled','fill_minute':b.timestamp.isoformat(),'fill_price':fill,
                    'events':events,'last_signal':current}
        close=b.timestamp+timedelta(minutes=1)
        if close.minute%15 or close.second:continue
        candle=lookup.get(close-timedelta(minutes=15))
        if candle is None:raise ValueError("Missing replacement-candle data")
        group=seen.get(candle.timestamp,[])
        if [m.timestamp for m in group]!=[candle.timestamp+timedelta(minutes=i) for i in range(15)]:
            events.append({'event':'incomplete_replacement_candle_requires_review','known_at':close.isoformat()})
            return {'status':'review_required','events':events,'last_signal':current}
        actual=(group[0].open,max(m.high for m in group),min(m.low for m in group),group[-1].close)
        if any(abs(a-b)>1e-8 for a,b in zip(actual,(candle.open,candle.high,candle.low,candle.close))):
            raise ValueError("Minute/replacement-candle OHLC mismatch")
        if not(candle.low<=zone.high and candle.high>=zone.low):
            events.append({'event':'replacement_outside_poi_requires_review','known_at':close.isoformat()})
            return {'status':'review_required','events':events,'last_signal':current}
        current={**current,'signal_bar_start':candle.timestamp.isoformat(),'available_at':close.isoformat(),
                 'entry_level':candle.high if side=='BUY' else candle.low,
                 'stop_level':candle.low if side=='BUY' else candle.high}
        events.append({'event':'pending_entry_and_stop_amended','known_at':close.isoformat(),
                       'entry_level':current['entry_level'],'stop_level':current['stop_level'],
                       'risk_recalculation_required':True})
    return {'status':'pending_at_data_end','events':events,'last_signal':current}


def scan_lc1_candidates(zone, candidates, minutes, quarters, context_approved):
    """Connect M15 candidate discovery to a supplied zone/context, not orders.

    Retain multiple points, deduplicate their qualifying reference pairs, and
    merge identical closed-candle signals. A level already taken before this
    setup's execution window cannot be silently reused as a fresh inducement.
    No distance, age, formation-type or PBID admission threshold is applied.
    """
    if not context_approved:
        return {'status':'context_not_approved','signals':[],'excluded':[],'reviews':[]}
    if not minutes:
        raise ValueError('Minute execution data required')
    for previous,current in zip(minutes,minutes[1:]):
        if current.timestamp<=previous.timestamp:
            raise ValueError('Minute data must be chronological and unique')
    start=max(zone.available_at,minutes[0].timestamp)
    end=minutes[-1].timestamp+timedelta(minutes=1)
    points={};excluded=[];reviews=[];signals={}
    for event in candidates:
        if event['status']!='qualified' or event['side']!=zone.side:continue
        if int(event.get('source_timeframe_minutes',0))!=15:
            raise ValueError('Only M15 entry-timeframe inducement candidates allowed')
        available=datetime.fromisoformat(event['available_at'])
        origin=datetime.fromisoformat(event['origin'])
        if available.tzinfo is None or origin.tzinfo is None or available<=origin:
            raise ValueError('Causal timezone-aware candidate times required')
        price=float(event['inducement_level'])
        if not math.isfinite(price) or price<=0:raise ValueError('Invalid inducement level')
        if available>=end:continue
        key=(event['origin'],price)
        if key not in points or available<points[key]['available']:
            points[key]={'origin':event['origin'],'level':price,'available':available,
                         'prior_reference':event['prior_reference']}
    for point in points.values():
        available=point['available'];price=point['level'];consumed=None;partial=False
        for bar in quarters:
            if bar.timestamp<available:continue
            if bar.timestamp>=start:break
            crossed=bar.high>price if zone.side=='SELL' else bar.low<price
            if crossed:
                if bar.timestamp+timedelta(minutes=15)>start:partial=True
                else:consumed=bar.timestamp
                break
        summary={**point,'available':available.isoformat()}
        if consumed is not None:
            excluded.append({**summary,'reason':'inducement_already_taken_before_setup_window',
                             'source_candle_start':consumed.isoformat()})
            continue
        if partial:
            reviews.append({**summary,'reason':'pre_window_sweep_order_requires_review'})
            continue
        result=scan_lc1(zone,LiquidityReference(price,available),minutes,quarters,True)
        if not result['signals']:
            unresolved=[e for e in result['events'] if 'review' in e['event']
                        or 'ambiguous' in e['event'] or 'incomplete' in e['event']]
            if unresolved:reviews.append({**summary,'events':unresolved})
            continue
        for signal in result['signals']:
            key=(signal['side'],signal['signal_bar_start'],signal['entry_level'],signal['stop_level'])
            if key not in signals:
                signals[key]={k:v for k,v in signal.items() if k!='inducement_distance_to_poi_pips'}
                signals[key]['scope']='Supplied POI/context; automatically discovered inducement; not a full strategy backtest'
                signals[key]['supporting_inducements']=[]
            signals[key]['supporting_inducements'].append({**summary,
                'distance_to_poi_pips':signal['inducement_distance_to_poi_pips']})
    return {'status':'signals_found' if signals else 'no_signal_or_review_required',
            'distinct_qualified_points':len(points),
            'signals':sorted(signals.values(),key=lambda s:s['available_at']),
            'excluded':excluded,'reviews':reviews,
            'scope':'Automatic inducement-to-LC-1 connection, with supplied zone/context; lifecycle after signals and full trade accounting not inferred'}
