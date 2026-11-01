"""Reconcile LC-1 sequence and accounting on two annotated examples, not a blind test."""

import argparse
from dataclasses import asdict
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path

from backtest import ROOT,read_bars
from fx_account import FXAccount,Quote
from reference_replay import replay
from swing_lc1 import hourly_bars,zone_after_break,qualify_inducement,scan_lc1,trace_pending_entry


CASES=[
    {'id':'round3_row3_2025_01_23','origin':'2025-01-23T12:00:00+00:00',
     'poi_broken_level_bar':'2025-01-23T09:00:00+00:00',
     'liquidity_bar':'2025-01-23T13:15:00+00:00',
     'liquidity_broken_level_timeframe':'15min','liquidity_broken_level_bar':'2025-01-23T13:00:00+00:00'},
    {'id':'round3_row4_2025_01_29','origin':'2025-01-29T01:00:00+00:00',
     'poi_broken_level_bar':'2025-01-28T14:00:00+00:00',
     'liquidity_bar':'2025-01-29T11:30:00+00:00',
     'liquidity_broken_level_timeframe':'15min','liquidity_broken_level_bar':'2025-01-29T09:00:00+00:00'},
]


def reconcile(quarters,minutes):
    hours=hourly_bars(quarters);h={b.timestamp:b for b in hours};q={b.timestamp:b for b in quarters}
    account=FXAccount();results=[]
    for case in CASES:
        origin=h[datetime.fromisoformat(case['origin'])]
        structure=h[datetime.fromisoformat(case['poi_broken_level_bar'])]
        if structure.timestamp+timedelta(hours=1)>origin.timestamp:
            raise ValueError('Annotated structure level is not available before origin')
        zone=zone_after_break(hours,origin,structure.low,'SELL')
        if zone is None:raise ValueError('No confirming close for reference POI')
        anchor=q[datetime.fromisoformat(case['liquidity_bar'])]
        prior=q[datetime.fromisoformat(case['liquidity_broken_level_bar'])]
        qualification=qualify_inducement(quarters,anchor,prior,'SELL')
        if qualification['status']!='qualified':
            raise ValueError(f"Annotated inducement needs review: {qualification['status']}")
        liquidity=qualification['liquidity']
        detection=scan_lc1(zone,liquidity,minutes,quarters,context_approved=True)
        if len(detection['signals'])!=1:raise ValueError('Reference did not produce one initial signal')
        initial=detection['signals'][0]
        pending=trace_pending_entry(initial,zone,minutes,quarters)
        if pending['status']!='filled':raise ValueError(f"Pending entry needs review: {pending['status']}")
        revisions=[initial]+[{**initial,'available_at':e['known_at'],'entry_level':e['entry_level'],
                    'stop_level':e['stop_level']} for e in pending['events']
                   if e['event']=='pending_entry_and_stop_amended']
        plans=[]
        for revision in revisions:
            available=datetime.fromisoformat(revision['available_at'])
            close=q[available-timedelta(minutes=15)].close
            quote=Quote(close-.005,close+.005)
            plan=account.plan('SELL',revision['entry_level'],revision['stop_level'],quote)
            plans.append({'at':available.isoformat(),**asdict(plan)})
        last=pending['last_signal'];signal=q[datetime.fromisoformat(last['signal_bar_start'])]
        path=replay(signal,minutes,'SELL',account.costs.spread_pips,account.costs.slippage_pips)
        if path.get('entry_minute_utc')!=pending['fill_minute'] or abs(path['entry_price']-pending['fill_price'])>1e-8:
            raise ValueError('Independent pending and exit replay disagree about entry')
        if path['status']!='closed':raise ValueError('Reference trade remains open in sample')
        bid=path['entry_price']+account.costs.slip
        account.open(case['id'],plan,path['entry_price'],Quote(bid,bid+.01))
        pnl=account.close(case['id'],path['exit_price'],path['exit_reason'])
        results.append({'annotated_inputs':case,'zone':asdict(zone),'liquidity':asdict(liquidity),
            'inducement_qualification':{**qualification,'liquidity':asdict(liquidity)},
            'scope':'Origin candle, reference structure levels and context approval are annotated inputs; not automatically selected',
            'detection':detection,'pending':pending,'risk_plans':plans,'execution':path,'accounting':pnl})
    return {'scope':'Two conditional reference reconciliations, NOT a full strategy or out-of-sample backtest',
        'limitations':['Phase/context approval and originating structure/POI/liquidity references are manual inputs',
            'Inducement is M15 only: opposite-level wick break qualifies, close adds quality. Origin/prior selection remains annotated; proximity is quality only, with no distance, left-leg-only or no-PBID admission filter',
            'Additional broken-level anchors test causality; they are candidate interpretations, not a confirmed general structure detector',
            'Late mitigation, replacement outside POI and ambiguous sequencing require review',
            'No automatic LC-2A/2B; gross-margin model, one-USD-unit sizing; no financing or broker liquidation'],
        'cases':results}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--context',type=Path,default=ROOT/'data/usdjpy_sample/USDJPY_context_15min.csv')
    p.add_argument('--minutes',type=Path,default=ROOT/'data/usdjpy_sample/USDJPY_execution_1min.csv')
    p.add_argument('--output',type=Path,default=ROOT/'data/strategy_review/lc1_sequence_reconciliation.json')
    args=p.parse_args()
    results=reconcile(read_bars(args.context),read_bars(args.minutes))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,indent=2,default=str),encoding='utf-8')
    for result in results['cases']:
        print(result['annotated_inputs']['id'],'initial signal',result['detection']['signals'][0]['available_at'],
              'amendments',len(result['risk_plans'])-1,'fill',result['pending']['fill_minute'],
              'exit',result['execution']['exit_reason'])
    print('Saved conditional reference checks:',args.output)


if __name__=='__main__':main()
