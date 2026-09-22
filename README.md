# SeabedNet

**Model-completed bathymetry, uncertainty and shoal hazard for Canadian waters, with every claim scored against data the model never saw.**

Under the 2,327 km Churchill–Atlantic shipping route that Canada, Manitoba and Saskatchewan are spending C$262.5M to reopen, 17% of the seabed carries a published sounding and the median survey year under the keel is **1974**. SeabedNet fills the rest: a masked-completion network trained on the Canadian Hydrographic Service NONNA archive with a gravity anchor, producing depth, a calibrated 1σ uncertainty and a provenance flag for every 100 m cell, plus a separate model for the shallowest point a keel could meet.

Public atlas: **https://girardemilio3-svg.github.io/churchill-corridor-atlas/** · technical report (PDF) in the same site under `/report/`.

> **Not a chart. Not for navigation.** This is a planning prior: it says where a survey ship should go first, and where the published chart is thin. Depths here are not verified and must not be used to navigate.

---

## Results

All numbers below are produced by the scripts in this repository and stored as JSON under [`results/`](results/). Nothing is retyped by hand.

### Depth completion, tested by hiding the future
Train on soundings published before 2016, predict the 6.46 million corridor soundings CHS has published since ([`results/temporal_validation_*.json`](results/), [`src/eval/temporal_eval.py`](src/eval/temporal_eval.py)).

| Model | Mean absolute error (m) |
|---|---|
| Nearest published sounding (baseline) | 18.85 |
| Gravity-derived bathymetry (baseline) | 18.08 |
| SeabedNet v5, published model | 13.26 |
| Full-size retrain, 4-fold test-time augmentation | 12.89 |
| Three-model ensemble | 12.83 |
| Ensemble + nearest-sounding blend inside 1 km | **12.45** |

The blend exists because of a defect this repository documents rather than hides: within about 500 m of an existing sounding, copying that sounding beats the model. Weights were fitted on half the corridor blocks and scored on the other half ([`src/eval/hybrid_eval.py`](src/eval/hybrid_eval.py)).

### Independent soundings, three ways
- **Research-cruise multibeam** (GMRT/NCEI archive, 386,685 cells in 17 blocks CHS has not published): model 9.6 m, nearest published sounding 30.4 m, gravity prior 6.1 m. Gravity wins in deep water, which is why inferred cells deeper than 400 m defer to it.
- **Ships of opportunity** (IHO crowdsourced bathymetry, ~450M pings 2017–2026, vessels calibrated against charted soundings): at 278,898 shelf cells with no charted sounding, model 4.9 m median error and 70% within 10 m; nearest charted sounding 3.2 m and 83%; the blended six-member map 3.4 m and 81%. The model wins beyond 1 km, loses inside it ([`src/eval/csb_eval2.py`](src/eval/csb_eval2.py)).
- **Groundings**, hindcast with only the soundings that existed before each ship struck: 5 of 7 documented Arctic strike sites fall in the top 10% of danger among water the chart called safe; 4 of 7 with a 10 km hole cut in the input ([`src/eval/hindcast_blind.py`](src/eval/hindcast_blind.py)).

### Where dangers get reported
A gradient-boosted model over the hazard field and its covariates, trained and tested on disjoint years of Coast Guard danger notices: AUC 0.942, with 83% of later reported dangers falling in the top-ranked tenth of chart-safe water ([`src/products/danger_model2.py`](src/products/danger_model2.py)).

### Prospective test, running now
Two forecasts were hashed, timestamped and published **before** any outcome existed ([`results/sealed/`](results/sealed/), [`src/products/prospective_forecast.py`](src/products/prospective_forecast.py)). The scoring rule was fixed in the same file at sealing time. Coast Guard notices issued afterwards score them ([`src/products/prospective_score.py`](src/products/prospective_score.py)).

First reading, one week in: the Arctic file has no eligible notice yet; the southern file has 10 notices inside it, 9 in the national top percentile. **Nine of those ten are one survey campaign in a bay with 132 prior notices in the training data**, so this counts as one hit on a recurring area, and the tenth notice is a miss at the 47th percentile. Two independent events so far. The files are re-scored weekly and the result is published either way.

### Results that did not work
Kept here deliberately, because a result list without them is not evidence.
- Coastal elevation and optical satellite imagery as extra input channels: no improvement, sometimes worse.
- A leakage-free gravity anchor: costs about 0.9 m, and that is the honest number to defend.
- Hazard heads trained from scratch, with and without radar: no better than the published head.
- ICESat-2 laser altimetry: cannot confirm or refute 3–7 m Arctic shoals. The detector finds nothing on 69 deep-water control passes and nothing reproducible on the claims ([`src/eval/is2_v2.py`](src/eval/is2_v2.py)).
- One sealed shoal claim is **refuted** by 613 ship soundings; of 15,936 unsealed hazard candidates, 217 have ship soundings nearby and 196 are refuted, none confirmed ([`results/candidates_vs_csb_summary.json`](results/candidates_vs_csb_summary.json)).

---

## Repository map

```
src/model        the completion network, its data pipeline, training loops (depth and hazard)
src/inference    national inference, ensembling, the distance blend, the standalone CLI tool
src/eval         every test above: temporal, independent multibeam, ship soundings, groundings,
                 laser altimetry, Coast Guard notices, uncertainty calibration
src/data         fetching and tiling NONNA, the gravity prior, radar and imagery channels,
                 survey-index dating, the crowdsourced-bathymetry crawler
src/products     shoal lists, the danger-report model, survey plans, sealed forecasts and scoring
src/site         builders for the public atlas and the technical report
scripts/pipeline the actual chains that produced the published models, in order
results/         every JSON result the atlas and report cite; sealed claims and their proofs
benchmark/       NONNA-Temporal-Churchill: a reusable held-out benchmark with a scoring script
```

## Running the model on your own soundings

No GPU required. See [`docs/RUNNING_THE_MODEL.md`](docs/RUNNING_THE_MODEL.md).

```bash
pip install torch numpy scipy rasterio
python3 src/inference/seabednet_complete.py --tif your_soundings.tif --out completed
```

Input is a grid of soundings in EPSG:3857 with nodata where you have none; output is completed depth, 1σ uncertainty and the provenance mask. To check it, hide a survey you hold, run the tool, and compare at the hidden cells. That is exactly the protocol in `src/eval/temporal_eval.py`.

Model weights are not in this repository (each is ~400 MB). They are available on request; the training recipe that produces them is `scripts/pipeline/`.

## Data sources

| Source | Use | Licence |
|---|---|---|
| CHS NONNA-100 / NONNA-10 (DFO) | training and test soundings | Open Government Licence – Canada |
| CHS Survey Index (DFO EGIS) | survey year and CATZOC for the temporal split | Open Government Licence – Canada |
| SRTM15+ / Sandwell (Scripps) | gravity-derived prior | public, cite the source |
| Copernicus GLO-30, Sentinel-1, Sentinel-2 | auxiliary channels | Copernicus, free and open |
| GMRT (Lamont-Doherty) / NCEI multibeam | independent test | open, cite the source |
| IHO DCDB crowdsourced bathymetry (NOAA NCEI) | independent test | public domain |
| Canadian Coast Guard NAVWARN notices | hazard and prospective tests | public |

NONNA is the published, non-navigational archive. CHS holds surveys that are not in it, so "no published sounding" never means "never surveyed", and this repository never claims otherwise.

## Limitations

1. Not navigational. No cell here meets IHO S-44 survey standards.
2. Inside roughly 500 m of a published sounding, the nearest sounding is the better estimate; the shipped map blends accordingly.
3. Uncertainty is calibrated on independent cells, but coverage is imperfect at the extremes of the σ range.
4. The hazard field over-predicts in busy, well-charted southern water, which is where it can be checked.
5. The Arctic claims remain untested: no ship-sounding pool covers them, and laser altimetry cannot resolve them.

## Citing

See [`CITATION.cff`](CITATION.cff). The benchmark is citable on its own: [`benchmark/README.md`](benchmark/README.md).

## Licence

Code: MIT ([`LICENSE`](LICENSE)). Results and documentation: CC BY 4.0. Source data keep the licences above.
