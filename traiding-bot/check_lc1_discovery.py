"""Offline LC-1 connection check: automatic inducement, annotated POI/context.

Expected liquidity origins/prices and signal times are not detection inputs.
Output signals still need context, pending-position and journal validation.
"""

import argparse
import csv
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from backtest import ROOT,read_bars
from check_swing_reference import CASES
from swing_lc1 import hourly_bars,zone_after_break,scan_lc1_candidates,trace_pending_entry


def check(quarters,minutes,candidates,reference_report=None):
    hours=hourly_bars(quarters);lookup={b.timestamp:b for b in hours}
    report={'scope':'Automatic M15 inducement-to-LC-1 connection; POI origin, broken HTF level and context remain supplied. No full strategy backtest.', 'cases':[]}
    for case in CASES:
        # Only the H1 zone inputs are used, not the annotated M15 liquidity.
        origin=lookup[datetime.fromisoformat(case['origin'])]
        prior=lookup[datetime.fromisoformat(case['poi_broken_level_bar'])]
        zone=zone_after_break(hours,origin,prior.low,'SELL')
        if zone is None:raise ValueError('Annotated zone has no confirming break')
        detection=scan_lc1_candidates(zone,candidates,minutes,quarters,True)
        pending=[]
        for signal in detection['signals']:
            trace=trace_pending_entry(signal,zone,minutes,quarters)
            pending.append({'signal_available_at':signal['available_at'],
                            'status':trace['status'],'fill_minute':trace.get('fill_minute'),
                            'amendments':sum(e['event']=='pending_entry_and_stop_amended'
                                             for e in trace['events'])})
        row={'case':case['id'],'annotated_zone':asdict(zone),
             'detection':detection,'pending_checks':pending}
        report['cases'].append(row)
    # Comparison occurs after all detection and is optional.
    if reference_report is not None:
        known={r['annotated_inputs']['id']:r['detection']['signals'][0]['available_at']
               for r in reference_report['cases']}
        for row in report['cases']:
            expected=known[row['case']]
            row['post_detection_reference_comparison']={
                'expected_initial_signal':expected,
                'expected_found':any(s['available_at']==expected for s in row['detection']['signals'])}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context',type=Path,required=True)
    parser.add_argument('--minutes',type=Path,required=True)
    parser.add_argument('--candidates',type=Path,required=True)
    parser.add_argument('--reference-report',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'data/strategy_review/lc1_automatic_inducement_connection.json')
    args=parser.parse_args()
    with args.candidates.open(newline='') as stream:candidates=list(csv.DictReader(stream))
    reference=json.loads(args.reference_report.read_text()) if args.reference_report else None
    report=check(read_bars(args.context),read_bars(args.minutes),candidates,reference)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,default=str)+'\n')
    for row in report['cases']:
        result=row['detection']
        print(json.dumps({'case':row['case'],'distinct_signals':len(result['signals']),
              'reviews':len(result['reviews']),
              'first_signals':[s['available_at'] for s in result['signals'][:5]],
              'first_pending_checks':row['pending_checks'][:3],
              'comparison':row.get('post_detection_reference_comparison')},indent=2))


if __name__=='__main__':main()
