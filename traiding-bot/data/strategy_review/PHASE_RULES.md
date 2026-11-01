# Phase rules transcribed from the user's supplied diagram

Source: Screenshot_2024-06-06_132439.png, right-hand MTF PHASES panel, visually
read at enlarged resolution. User explicitly pointed to this diagram for when
to take the phases. These are contextual conditions, not automatically numerical
or sufficient standalone signal definitions. No new backtest has been coded.

Always ask: What is the current objective? What has been mitigated?

## A — pro swing + pro internal

- Objective: target weak MTF swing high/low; play the MTF swing trend run.
- Full MTF alignment; swing pullback finished; follow internal structure.
- No additional MTF CHoCH required at MTF POI mitigation; go to the LTF entry model.
- Still require the user's qualifying POI and valid LC execution; alignment
  alone does not authorize an entry.

## B — pro swing + counter internal

- Objective: anticipate end of swing pullback and internal reversal.
- Best when swing pullback likely finishing, past swing equilibrium, and an
  extreme MTF/HTF POI at suitable premium/discount has been mitigated.
- Check enough reward/risk before internal supply/demand or a strong high/low.
- Waiting for MTF CHoCH is optional; consider unmitigated MTF/HTF POIs behind.
- If HTF suggests MTF may reverse, wait for MTF i-BOS (phase A).

## C — counter swing + pro internal

- Objective: play MTF swing pullback, or anticipate swing reversal if HTF supports it.
- Best after HTF POI mitigation, after MTF swing BOS, and at the start of the
  swing pullback before swing equilibrium.
- Waiting for MTF CHoCH is optional.

## D — counter swing + counter internal

- Very aggressive; source warns against this until consistently profitable.
- Objective: internal pullback, or anticipating internal reversal for a swing pullback.
- Favourable context listed: after MTF swing BOS when a swing pullback is expected
  (ideally avoid immediately after a swing pullback has just ended); HTF POI
  mitigation (a refined MTF POI is even better); MTF CHoCH from that mitigation;
  strong MTF liquidation; pro-HTF trend where HTF swing pullback is complete;
  enough reward/risk into a strong internal high/low.
- Source summary: either do not trade this phase, OR at minimum wait for an
  M15 CHoCH. Preserve the explicit M15 wording rather than silently replacing
  it with a 4H or 1H requirement.
- User journals do include phase-D trades and user has explained taking some as
  low probability, with exceptional reversal contexts potentially high probability.
  Therefore do not silently impose blanket exclusion, declare all D high quality,
  or treat a generic large candle as sufficient evidence. Any implementation must
  preserve the distinction between minimum entry confirmation and stronger context.

## Range

- When MTF/HTF intentions are unclear, stay out of the middle.
- Source suggestions: long at bottom 33%; short at top 33%; or wait for breakout.
- Do not invent a range-identification lookback or endpoints. These boundaries
  require defined swing/range construction before historical detection.

## Application to this plan

- User-selected hierarchy remains daily context, 4H/1H narrative/POIs, M15 execution.
- Preserve fixed 2R and other confirmed management rules. Context objectives
  such as targeting weak structure do not silently replace the confirmed exit.
- The diagram describes conditional discretion, not a universal phase-to-grade
  lookup. Grades still depend on POI/context and liquidity/mitigation evidence.
- Screenshot labels are reference annotations. Live/backtest phase assignment
  must use only structure confirmed by that time, not future candle reversals.
