# SeabedNet: Self-Supervised Generative Completion of a National Hydrographic Archive

**Emilio Girard** · Montréal · August 2026

## Abstract

We present the first learned completion of a national bathymetric survey archive. Using Canada's open CHS NONNA-100 dataset (429,682 km² of surveyed seafloor across three oceans and the Great Lakes), we train self-supervised models that reconstruct hidden seabed from surrounding survey context — masking real surveyed regions with realistic, survey-shaped gap patterns and validating against the held-out truth in metres. A heteroscedastic gated-convolution U-Net (v3) achieves **20.5 m MAE on three fully held-out regions (Placentia Bay NL, Juan de Fuca BC, Frobisher Bay NU) — 35% better than linear interpolation — with calibrated per-pixel uncertainty (94.8% of errors within 2σ after temperature scaling)**. Applying v3 to the full archive extends Canada's mapped seafloor by **+1,049,018 km²** of inference within 6 km of existing survey lines, each pixel carrying provenance (surveyed vs inferred) and calibrated σ. We report an honest negative result: a 38M-parameter conditional diffusion model (v2) *loses* to direct regression on point accuracy (30.0 m) and its sampling-spread uncertainty is miscalibrated (46% coverage) — regression wins the estimate; distribution modeling's residual value is realizations. We further find a predictability ceiling at 100 m resolution (~20 m MAE on 45–70% occlusions) and show that high-frequency seabed texture is largely irreducible at this scale, motivating a 4× super-resolution stage trained on NONNA-10. All outputs are planning priors with explicit uncertainty — never navigational products.

## 1. Data

CHS NONNA (Non-Navigational) bathymetry, Open Government Licence – Canada, retrieved via the public WCS service. National footprint discovered by a scaled full-extent request; 437 blocks (~2,000×2,000 px at 100 m nominal) covering every surveyed region. 43 named regional tiles for training/holdout curation. Land/datum artifacts (z > +25 m) masked. Web-Mercator area figures corrected by cos²(latitude).

## 2. Method

**Self-supervision.** Dense (>92% valid) patches are masked with three families: (a) real NONNA gap patterns harvested from sparse tiles, (b) random blocks, (c) half-plane survey edges. Loss applies only to hidden-but-known pixels. No labels required at any point.

**v1 (baseline):** 8.5M gated-conv U-Net, per-patch normalization, L1. **v2:** 38M conditional DDPM (cosine schedule, EMA, bf16), DDIM+RePaint sampling with SDEdit-style warm start. **v3 (production):** v1's architecture with a second head predicting log-variance, trained with Gaussian NLL + visible-L1 anchor; σ temperature-calibrated on a held-out split (c = 1.18).

**National inference:** overlapping windows (192 px, stride 96), Hann-blended μ and σ, Gaussian destriping of inferred regions only, predicted-land masking (fill > −4 m dropped), inference restricted to ≤6 km from real data.

## 3. Results (held-out regions, 45–70% occlusion)

| Model | MAE (m) | RMSE (m) | Uncertainty |
|---|---|---|---|
| Linear interpolation | 31.7 | 47.8 | — |
| v1 U-Net | 23.0 | 37.0 | — |
| v2 diffusion (mean-of-6) | 30.0 | 46.3 | corr 0.30, 46% ≤2σ (miscalibrated) |
| **v3 heteroscedastic** | **20.5** | **33.6** | **corr 0.58, 94.8% ≤2σ (calibrated)** |

**National application:** 429,682 km² surveyed → +1,049,018 km² completed (≤6 km from data), with provenance and σ per pixel.

## 4. Findings

1. **Regression beats diffusion for point estimates** on this task at this scale; the perception–distortion tradeoff measured from both sides.
2. **Calibration transfers:** σ temperature fitted on one mask distribution held (94.8%) on a harsher one.
3. **A predictability ceiling** (~20 m at 100 m/60% occlusion) that MAE-style metrics cannot push past — smoothness is often the *correct* conditional answer.
4. **Texture is a resolution question:** high-frequency energy in samples tracked *model error*, not seabed realism; genuine roughness modeling requires 10 m data (SeabedNet-SR).
5. **Sampling pathologies documented:** cosine-schedule terminal degeneracy (ᾱ≈2e-15 at t=T), DC-drift in large holes (fixed by warm-start), stale-ε inconsistency after x0 clamping.

## 5. Prior art

Fragments exist: DEM void-filling GANs (Gavriil 2019; Zhang 2020, terrestrial), bathymetry SR (Sonogashira 2020, 2×/450 m, Japan), GEBCO-grid VQ-VAE with conformal uncertainty (Minoza 2025, synthetic pairs), MBES-DDPM (2026, method-level). Global programs (GEBCO/Seabed 2030, NOAA BlueTopo) fill gaps via satellite-gravity inversion, survey splicing, or synthetic texture for visualization. **No prior work completes a national hydrographic archive with masked-real-survey self-supervision, held-out metric validation, provenance, and calibrated uncertainty.**

## 6. Limitations & ethics

Outputs are planning priors: they must never be used for navigation, and every product states this. Inference is restricted to the near-survey envelope; beyond it, the model's prior dominates and we decline to publish values. Residual survey-line striping can leak into reconstructions (mitigated, not eliminated). The 100 m national grid inherits NONNA's own datum and QC caveats ("raw data, no quality guarantee").

## 7. Super-resolution (preliminary)

A 2.3M-parameter residual SR network (×4, trained on 9 NONNA-10 regions, held-out Goldboro) improves on bicubic by 6% MAE (0.24 m vs 0.26 m) with modest visual sharpening; both remain smoother than native 10 m truth. Consistent with §4.4: recovering true fine-scale roughness likely requires spectral/adversarial objectives, not L1 SR. Reported as a preliminary/modest result.

## 8. Reproducibility

Entire pipeline (fetch → train → validate → complete → render) runs on one NVIDIA GB10 desktop from public data; v3 trains in ~2.5 h. Code: fetch_many/fetch_more/national_fetch, train_inpaint (v1), diffusion_v2 + sample_v2 (v2), train_v3 + v3_model (v3), national_complete, national_render2, train_sr (SR).
