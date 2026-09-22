#!/usr/bin/env python3
"""Survey planner: rank the corridor's highest-uncertainty boxes near the route.

Boxes of ~0.5°x0.25°, within 30 km of the Churchill route, ranked by total
uncertainty burden (mean σ × area). Output: SURVEY_PLAN.md + survey_plan.json.
Cost model (stated, conservative): multibeam coverage ~40 km²/day effective in
these depths; icebreaker/day C$205k (public CCGS figure from corridor brief).
"""
import glob, json, math, numpy as np
from scipy import ndimage as ndi
R = 6378137.0
def lat_of_y(y): return math.degrees(2*math.atan(math.exp(y/R))-math.pi/2)
def lon_of_x(x): return math.degrees(x/R)

LON0, LON1, LAT0, LAT1 = -102.0, -52.0, 53.0, 74.5
DPD = 20
Wc = int((LON1-LON0)*DPD); Hc = int((LAT1-LAT0)*DPD)
sgm = np.full((Hc, Wc), np.nan, np.float32)
for f in sorted(glob.glob("corridor_out/*.npz")):
    d = np.load(f, allow_pickle=True)
    c = d["complete"].astype("float32"); k = d["known"].astype(bool)
    s = d["sigma"].astype("float32"); bb = d["bbox3857"]
    H, W = c.shape
    fill = np.isfinite(c) & ~k & (ndi.distance_transform_edt(~k) <= 60)
    D = 10
    Hs, Ws = (H//D)*D, (W//D)*D
    with np.errstate(all="ignore"):
        sS = np.nanmean(np.nanmean(np.where(fill, s, np.nan)[:Hs,:Ws].reshape(Hs//D,D,Ws//D,D),3),1)
    hh, ww = sS.shape
    lo0, lo1 = lon_of_x(bb[0]), lon_of_x(bb[2]); la0, la1 = lat_of_y(bb[1]), lat_of_y(bb[3])
    rows = ((LAT1-np.linspace(la1, la0, hh))*DPD).astype(int)
    cols = ((np.linspace(lo0, lo1, ww)-LON0)*DPD).astype(int)
    ok = (rows>=0)&(rows<Hc); okc = (cols>=0)&(cols<Wc)
    if not ok.any() or not okc.any(): continue
    rr, cc = np.meshgrid(rows[ok], cols[okc], indexing="ij")
    cur = sgm[rr, cc]; src = sS[ok][:,okc]
    sgm[rr, cc] = np.where(np.isfinite(src), src, cur)

ROUTE = [(-94.19,58.77),(-92.0,59.6),(-88.5,60.8),(-84.0,62.2),(-80.5,62.9),
         (-74.5,62.6),(-68.5,61.9),(-64.5,60.9),(-60.0,59.3),(-56.5,57.5)]
# distance-to-route mask (in canvas px), route densified
pts = []
for (a,b),(c2,d2) in zip(ROUTE[:-1], ROUTE[1:]):
    for t in np.linspace(0,1,60):
        pts.append((a+(c2-a)*t, b+(d2-b)*t))
rmask = np.zeros((Hc, Wc), bool)
for lo, la in pts:
    r = int((LAT1-la)*DPD); c2 = int((lo-LON0)*DPD)
    if 0 <= r < Hc and 0 <= c2 < Wc: rmask[r, c2] = True
near_route = ndi.distance_transform_edt(~rmask) <= (30/5.55/ (111/DPD) * (DPD/20) * 20/111*111)  # ~30km
near_route = ndi.distance_transform_edt(~rmask) * (111.0/DPD) <= 35   # px->km approx (lat)

BOX = 10  # 10px = 0.5deg lon x 0.5deg lat at DPD 20
rows = []
for i in range(0, Hc-BOX, BOX):
    for j in range(0, Wc-BOX, BOX):
        sel = sgm[i:i+BOX, j:j+BOX]
        nr = near_route[i:i+BOX, j:j+BOX]
        val = np.isfinite(sel) & nr
        if val.sum() < 8: continue
        la = LAT1 - (i+BOX/2)/DPD; lo = LON0 + (j+BOX/2)/DPD
        cellkm2 = (111.0/DPD)*(111.0/DPD*math.cos(math.radians(la)))
        area = float(val.sum())*cellkm2
        ms = float(np.nanmean(np.where(val, sel, np.nan)))
        ps = float(np.nanmax(np.where(val, sel, np.nan)))
        rows.append(dict(lat=round(la,2), lon=round(lo,2), area_km2=round(area),
                         mean_sigma=round(ms,1), peak_sigma=round(ps,1),
                         burden=round(ms*area)))
rows.sort(key=lambda r: -r["burden"])
top = rows[:10]
RATE = 40.0; DAY = 183000
for r in top:
    r["ship_days"] = round(r["area_km2"]/RATE, 1)
    r["cost_CAD_M"] = round(r["ship_days"]*DAY/1e6, 2)
json.dump(top, open("survey_plan.json","w"), indent=1)
md = ["# Churchill Corridor — Survey Priority Plan (SeabedNet v5 σ-ranked)\n",
      "Top 10 uncertainty boxes within ~35 km of the Churchill route, ranked by total",
      "uncertainty burden (mean σ × inferred area). Where a survey ship earns its day rate first.\n",
      "| # | Lat | Lon | Inferred area (km²) | mean σ (m) | peak σ (m) | Ship-days | Cost (C$M) |",
      "|---|-----|-----|----|----|----|----|----|"]
for n, r in enumerate(top, 1):
    md.append(f"| {n} | {r['lat']} | {r['lon']} | {r['area_km2']:,} | {r['mean_sigma']} | "
              f"{r['peak_sigma']} | {r['ship_days']} | {r['cost_CAD_M']} |")
md += ["", f"Assumptions: multibeam effective coverage {RATE:.0f} km²/day in corridor depths; "
       f"icebreaker day rate C${DAY:,} (CCG PC3 charter, July 2026: C$22M / ~120 days). σ from SeabedNet v5-small "
       "(rank-valid, corr 0.63 with true error; uncalibrated). Planning prior — NOT for navigation.",
       f"Total top-10: {sum(r['area_km2'] for r in top):,} km², "
       f"{sum(r['ship_days'] for r in top):.0f} ship-days, C${sum(r['cost_CAD_M'] for r in top):.1f}M "
       "— versus 'more than a decade' (CHS) for full-corridor conventional coverage."]
open("SURVEY_PLAN.md","w").write("\n".join(md))
print("\n".join(md[4:16]))
print("PLANNER_DONE")
