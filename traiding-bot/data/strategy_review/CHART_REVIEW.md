# Chart archive intake and first visual review

## Inventory verified

- Both uploaded ZIPs extracted safely.
- Part 01: 241 chart files; Part 02: 80 chart files.
- 321 files match all 321 links indexed from the 109 dated journal rows.
- Per workbook: Round 1 170; Round 2 45; Round 3 106.
- Column labels: daily_4h 106, one_hour 107, entry_15min 108.
  These labels come from workbook columns, not an independent image timeframe check.
- 307 unique image byte hashes; 14 repeated copies beyond the first occurrence.
  Preserve duplicate links and source rows; a duplicate screenshot does not prove
  the trade is a duplicate.
- Six chart slots across the 109 x 3 nominal grid had no link in the original
  workbooks. No additional image is missing from the downloader's linked inventory.
- Detailed source map: chart_manifest.json (journal fields and original URLs),
  charts/manifest.json (downloaded image filenames).

## First visual review — bounded coverage

Fifteen images from six records were opened at full image resolution. This is
an initial comparative sample, NOT a completed visual review of all 321 files.
Selection includes different years, setup models, phases and recorded outcomes.
Do not use outcomes to label pre-entry setup quality.

| Record | Images opened | Observations, not new rules |
|---|---|---|
| Round 3 row 4, 2025-01-29, LC-1, HIGH, phase A | 4H, 1H, 15M | 4H annotations show downward internal breaks; 1H supply rectangle; 15M dotted liquidity reference and short-position drawing. Useful aligned-short example. |
| Round 3 row 3, 2025-01-23, LC-1, MED, phase C | 1H, 15M | 1H supply rectangle and marked structure. 15M short drawing with multiple candles near/within supply. Recorded loss remains a candidate valid setup, not automatically an invalid example. |
| Round 2 row 7, 2024-03-12, LC-2A, HIGH, phase C | 1H, 15M | 1H upward internal breaks following a decline, local demand area and higher supply area. 15M downward sweep into demand, long-position drawing and subsequent rally. Requires precise pre-entry trend/confirmation reconciliation. |
| Round 1 row 16, 2023-03-26, LC-2B, MED, phase D | 1H, 15M | Broader descending context with local bullish internal leg and demand. Multiple dotted liquidity references on entry chart. Confirms LC-2B examples are available. |
| Round 1 row 4, 2023-01-03, LC-1, LOW, phase D | 4H, 1H, 15M | Downward broader context; entry image contains both a preceding short drawing and a later long drawing. A chart-to-row link is not always a one-position image. Need match by entry timestamp/side rather than infer from any visible trade drawing. |
| Round 2 row 3, 2024-01-08, LC-1, MED, phase C | 4H, 1H, 15M | Several marked structure levels/zones on higher charts; local supply and short-position drawing on entry chart. Good example of distinguishing broader narrative from immediate entry direction. |

## Findings for the specification

- These annotated charts support a structure/zone/liquidity strategy; do not
  replace the user's model with generic SMA signals or fixed-colour candles.
- Both long and short examples, more than one setup model, and phases A/C/D
  appear. User's CURRENT eligibility should not be inferred from a recorded
  trade or its profit. Earlier journals may include now-excluded noisy contexts.
- Higher-timeframe charts show several valid price areas simultaneously,
  consistent with the user's confirmation of multiple and mid-leg POIs.
- Some images show multiple trade drawings or duplicated screenshots across
  rows/timeframe columns. Resolve individual entries using journal date/time;
  do not extract an arbitrary drawing as the recorded trade.
- Screenshots include post-entry candles and possibly annotations made later.
  They are reference labels, not proof of what was known at signal time. Test
  logic must confirm pivots/zones using only data available before each entry.
- The images are labelled OANDA on FXReplay. Future raw-data choice must account
  for feed differences if using IBKR; matching timestamps, candles, spreads and
  price triggers cannot be assumed across feeds.
- Screenshot OHLC values in headers refer to a displayed/selected candle, not
  necessarily the POI or entry candle. Do not read them as historical entry prices.
- Screenshot evidence alone cannot establish bid/ask execution, tick ordering,
  financing, or complete order amendment history.

## Next targeted validation

Use exact journal row references for any questions, avoiding a request to upload
the same charts again. Establish which historical trades remain admissible under
the current noise/phase filter, independent of their eventual result. Then use
pre-entry cropped examples to reconcile structure, POI origin, liquidation and
order amendment step by step before implementing detection or testing new data.

No full independent strategy backtest has been run from these charts.
