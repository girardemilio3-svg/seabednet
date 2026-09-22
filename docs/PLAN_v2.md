# SeabedNet v2 plan — from atlas to evidence (Sept 2026)

## Thesis (the novel part)

Every bathymetry-completion model — ours included — predicts **mean depth**. Ships do not
ground on the mean. They ground on the **shallowest point inside the swept path**: an
unresolved pinnacle, a boulder, a moraine crest. Canadian Shield seabed is glacial terrain
with heavy-tailed roughness; the mean is the wrong target for the only question that
matters. Three moves follow, and nobody has put them together:

1. **Predict the extreme, not the mean.** New target: for each cell, the distribution of
   the *minimum* depth within r = 250/500/1000 m. Ground truth exists for free: NONNA-10
   (10 m) vs NONNA-100 (100 m) pairs give the sub-grid extreme statistics wherever both
   exist. Output = P(shoal < draft) per cell — a hazard field, not a depth map. This is
   the quantity a navigator, an insurer, and CHS's survey planner actually need.

2. **Hindcast the groundings.** Every Arctic grounding on an "uncharted shoal" in the TSB
   record is a natural experiment: Thamesborg 2025 (Franklin Strait), Akademik Ioffe 2018
   (Kugaaruk), Clipper Adventurer 2010 (Coronation Gulf), the Nanny groundings 2010/12/14
   (Simpson Strait), Hanseatic 1996. Train with post-incident surveys withheld; ask: does
   the hazard field rank the strike site in the top X% of the corridor? A benchmark that
   did not exist, on public data, that any future model can be scored against.

3. **A free sensor that only sees the dangerous depths.** Grounded ice ridges (stamukhi)
   and landfast-ice anchor points pin at 15–25 m — exactly freighter grounding depth —
   and are visible every winter in Sentinel-1 SAR (free, whole corridor, 12-day repeat).
   Multi-winter persistence of grounded features = shoal detector in the one depth band
   the archive is worst at. Fuse it as a conditioning channel + validation signal.
   Sentinel-2 optical SDB covers 0–15 m in clear water; soundings cover the rest.

Framing: "The archive predicts the mean; groundings are caused by the extreme. We predict
the extreme, validate it on the groundings that happened, and add a satellite sensor
that only sees the water that sinks ships."

## Validation program (what makes it evidence)

| Source | What | Independence | Status |
|---|---|---|---|
| NCEI multibeam archive: 10 Amundsen collections 2003–13 (~240k track-km, EM300/302), Healy, Knorr, Armstrong, Merian | swath depths, dated | Research cruises, not CHS holdings; verify per-tile | 36 surveys intersect corridor bbox — endpoints confirmed |
| GMRT GridServer (`layer=topo-mask`) | gridded multibeam with cruise attribution | Non-CHS cruises only | **Working** — 578 val cells in Thamesborg block already |
| IHO DCDB CSB API | crowdsourced soundings, timestamped | Not in NONNA | Endpoint located, sparse |
| NONNA BAG format | embeds survey-date metadata | same archive — enables **temporal holdout** | to fetch |
| IBCAO 5.2 source CSV | per-contribution cruise list | strip NONNA-attributed, keep Amundsen/Oden/Healy | to fetch (50 GB) |

Deliverable: `validation_report.md` — MAE/bias/σ-calibration by distance-to-sounding on
*independent* depths, stratified, plus the grounding hindcast table.

## Corrections to the live page (today)
- Exhibit D: "75%" → "55% of the water in this block has no published sounding";
  add the σ-at-the-site finding (98th percentile, 1.7 km beyond the surveyed swath).
- "unsurveyed" → "no published sounding" everywhere (NONNA ≠ all CHS holdings).
- $262.5M: federal $180M + Manitoba + Saskatchewan.
- Trust grade A/B/C on the keel profile by distance to nearest sounding.
- Day rate C$205k → C$183k/day (CCG PC3 charter, July 2026: C$22M / ~120 d); 40 km²/day stays, labelled assumption.
- Headline context: 15.8% of Canadian Arctic waters adequately surveyed, 44.7% of key routes (CHS via IHO Review, Dec 2025); "more than a decade" = Leyzack, Hakai, May 2016 — a decade ago.
- Vessel density: DFO NW Atlantic AIS density series (2013–24) reaches Hudson Strait entrance only; Hudson Bay interior unconfirmed.

## Build order
| # | Work | Compute | Days |
|---|---|---|---|
| 1 | Page corrections + trust grade | Spark | 0.5 |
| 2 | Independent validation: Amundsen/GMRT/CSB harvest, regrid, score v5 corridor + Canada | Spark | 2 |
| 3 | Official adequacy overlay: CHS Survey Index (egisp.dfo-mpo.gc.ca …/chs_edh_survey_index/MapServer) + DFO Vessel Traffic Routes vs found channel (NLISC polygons not public — ask OPPCorridorsPPO@tc.gc.ca) | Spark | 0.5 |
| 4 | σ calibration (isotonic on held-out + independent) | Spark | 0.5 |
| 5 | Extreme-depth target: NONNA-10/100 pair dataset, train v6-extreme head | **5090 spot, ~$2–4 — ask first** | 2 |
| 6 | Grounding hindcast benchmark (5 incidents, withheld surveys) | Spark | 1.5 |
| 7 | Sentinel-1 grounded-ice channel (corridor only, 3 winters) | Spark | 3 |
| 8 | Rebuild atlas: hazard field + validation + hindcast + corridor overlay | — | 1 |
| 9 | MPO intake + CHS courtesy note + public falsifiable forecast (hashed) | — | 0.5 |

## The ask (MPO form / CHS)
Not "look at my map." Ask: (a) access to CHS's unpublished multibeam for the Churchill
corridor under a validation agreement — we score the model on it, publish the score;
(b) a charting-risk budget line in Churchill Plus, priced by the σ-ranked survey plan;
(c) Arctic Gateway as the partner whose file this is.

## Rules in force
No GPU rental without OK. No touching user's instances or sessions. RAM cap 118 GB.
