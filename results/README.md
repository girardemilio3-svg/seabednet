# Results

Every JSON the atlas and the technical report cite, written by the scripts in `src/`. No number in this repository is typed by hand.

- `temporal_validation_*.json` — the hide-the-future benchmark for each model variant (`src/eval/temporal_eval.py`, `ensemble_temporal.py`, `hybrid_eval.py`).
- `indep_validation_*.json`, `baselines.json`, `gebco_eval.json` — independent research-cruise multibeam and the stronger interpolation baselines.
- `csb_shelf_stats*.json`, `candidates_vs_csb_summary.json` — ship-of-opportunity soundings against the map and against the claims.
- `hindcast*.json` — grounding hindcasts, all-visible and blind.
- `navwarn_*.json`, `danger_model*.json`, `national_plan*.json` — Coast Guard danger notices, the danger-report model, survey plans.
- `is2_v2.json` — laser altimetry, with the deep-water controls that make its null meaningful.
- `sigma_calibration.json` — uncertainty calibration on independent cells.
- `prospective_score_*.json` — the running score of the sealed forecasts.

## sealed/

Claims published before they could be checked, each with its SHA-256 in the matching manifest and an OpenTimestamps proof (`.ots`) anchoring the hash to the Bitcoin blockchain. Verify with `ots verify <file>.ots`.

- `shoal_list_v2_2026-09-06.csv` — 40 positions where the model says a keel-depth shoal hides in water the chart calls safe. One has since been refuted by ship soundings; it stays on the list, marked.
- `forecast_2026-09-02.csv`, `strike_predictions_2026-09-03.csv` — earlier sealed products.
- `forecast_danger_*.json` — manifests for the two prospective danger forecasts (cell files are ~250–480 MB and are available on request; the manifest carries the hash that identifies them).

## navwarn/

Parsed Coast Guard danger notices used as test outcomes, with their source message ids.
