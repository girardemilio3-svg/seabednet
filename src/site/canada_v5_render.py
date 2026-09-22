#!/usr/bin/env python3
"""Churchill Corridor Atlas — hero render.

Panel 1 (corridor_hero.png): provenance map — blue surveyed / amber v5 inference,
Churchill->Atlantic route, Thamesborg grounding site.
Panel 2 (corridor_sigma.png): per-pixel uncertainty of the inferred seabed —
the insurers' map (uncertainty, not ice, is the season-limiter).
"""
import glob, math, numpy as np, json
from scipy import ndimage as ndi
R = 6378137.0
def lat_of_y(y): return math.degrees(2*math.atan(math.exp(y/R))-math.pi/2)
def lon_of_x(x): return math.degrees(x/R)

LON0, LON1, LAT0, LAT1 = -142.0, -50.0, 40.0, 84.0
DPD = 40
Wc = int((LON1-LON0)*DPD); Hc = int((LAT1-LAT0)*DPD)
srv = np.full((Hc, Wc), np.nan, np.float32)
fil = np.full((Hc, Wc), np.nan, np.float32)
sgm = np.full((Hc, Wc), np.nan, np.float32)
sv = fl = 0.0
for f in sorted(glob.glob("national_v5_out/*.npz")):
    d = np.load(f, allow_pickle=True)
    c = d["complete"].astype("float32"); k = d["known"].astype(bool)
    s = d["sigma"].astype("float32"); bb = d["bbox3857"]
    H, W = c.shape
    dist = ndi.distance_transform_edt(~k)
    fill = np.isfinite(c) & ~k & (dist <= 60)
    lat = lat_of_y((bb[1]+bb[3])/2); corr = math.cos(math.radians(lat))**2
    sv += float(k.sum())*0.011236*corr; fl += float(fill.sum())*0.011236*corr
    D = 3
    Hs, Ws = (H//D)*D, (W//D)*D
    def sh(a):
        with np.errstate(all="ignore"):
            return np.nanmean(np.nanmean(a[:Hs,:Ws].reshape(Hs//D,D,Ws//D,D),3),1)
    sB = sh(np.where(k, c, np.nan)); sF = sh(np.where(fill, c, np.nan))
    sS = sh(np.where(fill, s, np.nan))
    hh, ww = sB.shape
    lo0, lo1 = lon_of_x(bb[0]), lon_of_x(bb[2])
    la0, la1 = lat_of_y(bb[1]), lat_of_y(bb[3])
    rows = ((LAT1-np.linspace(la1, la0, hh))*DPD).astype(int)
    cols = ((np.linspace(lo0, lo1, ww)-LON0)*DPD).astype(int)
    ok = (rows>=0)&(rows<Hc); okc = (cols>=0)&(cols<Wc)
    if not ok.any() or not okc.any(): continue
    rr, cc = np.meshgrid(rows[ok], cols[okc], indexing="ij")
    for canvas, src in [(srv, sB[ok][:,okc]), (fil, sF[ok][:,okc]), (sgm, sS[ok][:,okc])]:
        cur = canvas[rr, cc]
        canvas[rr, cc] = np.where(np.isfinite(src), src, cur)

print(f"canada: surveyed {sv:,.0f} km2  inferred(<=6km) {fl:,.0f} km2")
json.dump({"surveyed_km2": sv, "inferred_km2": fl}, open("canada_v5_stats.json", "w"))

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

# land + unmapped-water context from the gravity/topo grid
_g = np.load("planetary/gravity_prior_canada.npz")
_gz = _g["z"]; _glon = _g["lon"]; _glat = _g["lat"]
_cl = np.linspace(LON0, LON1, Wc); _ca = np.linspace(LAT1, LAT0, Hc)
_gx = np.clip((_cl-_glon[0])/(_glon[1]-_glon[0])*(_gz.shape[1]-1), 0, _gz.shape[1]-1).astype(int)
_gy = np.clip((_ca-_glat[0])/(_glat[1]-_glat[0])*(_gz.shape[0]-1), 0, _gz.shape[0]-1).astype(int)
topo = _gz[np.ix_(_gy, _gx)]
land = topo > 0

def paint_context(ax, ext):
    water = np.zeros((Hc, Wc, 4)); water[..., 0:3] = (0.024, 0.039, 0.078); water[..., 3] = 1.0
    ax.imshow(water, extent=ext, origin="upper", aspect=2.1, zorder=0)
    lrgb = np.zeros((Hc, Wc, 4))
    shade = np.clip(topo/2500.0, 0, 1)*0.10
    for i, base in enumerate((0.10, 0.12, 0.15)):
        lrgb[..., i] = base + shade
    lrgb[..., 3] = np.where(land, 1.0, 0.0)
    ax.imshow(lrgb, extent=ext, origin="upper", aspect=2.1, zorder=1)

ROUTE = [(-94.19,58.77),(-92.0,59.6),(-88.5,60.8),(-84.0,62.2),(-80.5,62.9),
         (-74.5,62.6),(-68.5,61.9),(-64.5,60.9),(-60.0,59.3),(-56.5,57.5)]
CHURCHILL = (-94.19, 58.77)
THAMESBORG = (-96.8, 70.6)   # Franklin Strait, approx — Sept 2025 grounding

def base_fig():
    fig, ax = plt.subplots(figsize=(16.2, 15.4), dpi=130)
    fig.patch.set_facecolor("#04060c"); ax.set_facecolor("#04060c"); ax.set_axis_off()
    ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1)
    ax.set_position([0.0, 0.075, 1.0, 0.875])
    return fig, ax

def annotate(ax):
    xs, ys = zip(*ROUTE)
    ax.plot(xs, ys, color="#8ef0c0", lw=2.2, ls=(0,(6,3)), alpha=0.9, zorder=6)
    ax.scatter(*CHURCHILL, s=180, marker="*", color="#ffd24d", edgecolor="k", zorder=7)
    ax.annotate("PORT OF CHURCHILL", CHURCHILL, xytext=(8,-16),
                textcoords="offset points", color="#ffd24d", fontsize=11, weight="bold")
    ax.scatter(*THAMESBORG, s=150, marker="X", color="#ff5d5d", edgecolor="k", zorder=7)
    ax.annotate("MV THAMESBORG grounding\nFranklin Strait, Sept 2025 (approx.)", THAMESBORG,
                xytext=(10,8), textcoords="offset points", color="#ff9d9d", fontsize=10)

# panel 1: provenance
fig, ax = base_fig()
vmin = np.nanpercentile(np.where(np.isfinite(srv), srv, np.nan), 3)
def norm(a): return np.clip((a-vmin)/(0-vmin+1e-9), 0, 1)
rgbs = plt.cm.Blues_r(norm(srv)*0.70+0.05); rgbs[...,3] = np.where(np.isfinite(srv),1,0)
rgbf = plt.cm.YlOrBr_r(norm(fil)*0.55+0.30); rgbf[...,3] = np.where(np.isfinite(fil),0.95,0)
ext = [LON0, LON1, LAT0, LAT1]
paint_context(ax, ext)
ax.imshow(rgbf, extent=ext, origin="upper", aspect=2.1, zorder=2)
ax.imshow(rgbs, extent=ext, origin="upper", aspect=2.1, zorder=3)
ax.set_title("CANADA, COMPLETED — blue: surveyed (CHS archive) · amber: SeabedNet v5 inference",
             color="white", fontsize=14.5, weight="bold", loc="left", pad=12)
fig.text(0.02, 0.055, f"{sv:,.0f} km² surveyed → +{fl:,.0f} km² completed within 6 km of survey lines · "
         f"v5: 10.53 m held-out MAE, 48% better than gravity physics near soundings, matches it beyond · per-pixel σ",
         color="#cfd8ea", fontsize=11)
fig.text(0.02, 0.02, "CHS NONNA-100, Open Government Licence · SeabedNet v5-small, Montréal · planning prior — NOT for navigation",
         color="#66779a", fontsize=8.5)
fig.savefig("canada_v5_hero.png", dpi=130, facecolor="#04060c", bbox_inches="tight")
print("HERO_DONE")

# panel 2: uncertainty
fig, ax = base_fig()
smax = np.nanpercentile(np.where(np.isfinite(sgm), sgm, np.nan), 97)
rgbu = plt.cm.magma(np.clip(sgm/(smax+1e-9), 0, 1)); rgbu[...,3] = np.where(np.isfinite(sgm), 1, 0)
rgbk = np.zeros((*srv.shape, 4)); rgbk[...,0:3] = 0.16; rgbk[...,3] = np.where(np.isfinite(srv), 1, 0)
paint_context(ax, ext)
ax.imshow(rgbk, extent=ext, origin="upper", aspect=2.1, zorder=2)
ax.imshow(rgbu, extent=ext, origin="upper", aspect=2.1, zorder=3)
ax.set_title("WHERE CANADA IS STILL UNCERTAIN — per-pixel σ of the inferred seabed (dark grey: surveyed)",
             color="white", fontsize=14.5, weight="bold", loc="left", pad=12)
fig.text(0.02, 0.055, f"bright = highest σ (up to ~{smax:.0f} m) — the exact places a survey ship earns its day rate first",
         color="#cfd8ea", fontsize=11)
fig.text(0.02, 0.02, "SeabedNet v5-small σ (uncalibrated, rank-valid: corr 0.63 with true error) · planning prior — NOT for navigation",
         color="#66779a", fontsize=8.5)
fig.savefig("canada_v5_sigma.png", dpi=130, facecolor="#04060c", bbox_inches="tight")
print("SIGMA_DONE")
print("ATLAS_RENDER_DONE")
