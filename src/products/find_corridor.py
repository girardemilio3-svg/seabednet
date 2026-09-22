#!/usr/bin/env python3
"""FIND the Churchill corridor: least-risk path Churchill -> Atlantic through
the completed depth + sigma fields (Dijkstra over the corridor mosaic).

Cost per km of track = 1 (distance)
  + shallow penalty (blocks <20 m, punishes <50 m — ice-class freighter water)
  + sigma penalty (sigma/8 — uncertainty is risk)
  + no-data penalty (x12 — crossable only when there is no alternative)
Land and dry cells: impassable.
Outputs: corridor_found.json (the path), corridor_found.png (path vs naive route).
"""
import glob, heapq, json, math, numpy as np
from scipy import ndimage as ndi
R = 6378137.0
def lat_of_y(y): return math.degrees(2*math.atan(math.exp(y/R))-math.pi/2)
def lon_of_x(x): return math.degrees(x/R)

LON0, LON1, LAT0, LAT1 = -102.0, -52.0, 53.0, 74.5
DPD = 12   # ~9 km cells — channel-scale, keeps Dijkstra fast
Wc = int((LON1-LON0)*DPD); Hc = int((LAT1-LAT0)*DPD)
dep = np.full((Hc, Wc), np.nan, np.float32)
sig = np.full((Hc, Wc), np.nan, np.float32)
knw = np.zeros((Hc, Wc), bool)
for f in sorted(glob.glob("corridor_out/*.npz")):
    d = np.load(f, allow_pickle=True)
    c = d["complete"].astype("float32"); k = d["known"].astype(bool)
    s = d["sigma"].astype("float32"); bb = d["bbox3857"]
    H, W = c.shape
    fill = np.isfinite(c) & ~k & (ndi.distance_transform_edt(~k) <= 60)
    use = k | fill
    D = 16
    Hs, Ws = (H//D)*D, (W//D)*D
    def sh(a):
        with np.errstate(all="ignore"):
            return np.nanmean(np.nanmean(a[:Hs,:Ws].reshape(Hs//D,D,Ws//D,D),3),1)
    # conservative: use the SHALLOWEST depth in each cell, not the mean
    with np.errstate(all="ignore"):
        dmin = np.nanmax(np.where(use, c, np.nan)[:Hs,:Ws].reshape(Hs//D,D,Ws//D,D), axis=(1,3))
    sS = sh(np.where(fill, s, np.nan)); kS = sh(k.astype(np.float32))
    hh, ww = dmin.shape
    lo0, lo1 = lon_of_x(bb[0]), lon_of_x(bb[2]); la0, la1 = lat_of_y(bb[1]), lat_of_y(bb[3])
    rows = ((LAT1-np.linspace(la1, la0, hh))*DPD).astype(int)
    cols = ((np.linspace(lo0, lo1, ww)-LON0)*DPD).astype(int)
    ok = (rows>=0)&(rows<Hc); okc = (cols>=0)&(cols<Wc)
    if not ok.any() or not okc.any(): continue
    rr, cc2 = np.meshgrid(rows[ok], cols[okc], indexing="ij")
    src_d = dmin[ok][:,okc]; src_s = sS[ok][:,okc]; src_k = kS[ok][:,okc]
    upd = np.isfinite(src_d)
    dep[rr, cc2] = np.where(upd, src_d, dep[rr, cc2])
    sig[rr, cc2] = np.where(np.isfinite(src_s), src_s, sig[rr, cc2])
    knw[rr, cc2] |= (src_k > 0.5)

# land / open-unknown from topo
g = np.load("planetary/gravity_prior_canada.npz")
gz = g["z"]; glon = g["lon"]; glat = g["lat"]
cl = np.linspace(LON0, LON1, Wc); ca = np.linspace(LAT1, LAT0, Hc)
gx = np.clip((cl-glon[0])/(glon[1]-glon[0])*(gz.shape[1]-1), 0, gz.shape[1]-1).astype(int)
gy = np.clip((ca-glat[0])/(glat[1]-glat[0])*(gz.shape[0]-1), 0, gz.shape[0]-1).astype(int)
topo = gz[np.ix_(gy, gx)]
land = topo > 0

# per-cell traversal multiplier
mult = np.full((Hc, Wc), np.inf, np.float32)
have = np.isfinite(dep)
water = ~land
pen = np.zeros((Hc, Wc), np.float32)
d_eff = np.where(have, dep, np.nan)
pen_sh = np.where(d_eff > -20, np.inf, np.where(d_eff > -50, 8.0, np.where(d_eff > -100, 1.5, 0.0)))
pen_sg = np.nan_to_num(sig, nan=0.0)/8.0
mult = np.where(have & water, 1.0 + pen_sh + pen_sg, mult)
mult = np.where(~have & water, 13.0, mult)          # crossable unknown water
mult = np.where(land, np.inf, mult)

def cell(lo, la): return int((LAT1-la)*DPD), int((lo-LON0)*DPD)
SRC = cell(-94.10, 58.80); DST = cell(-56.5, 57.5)
# nudge endpoints to nearest finite-cost cell
def nearest_ok(p):
    r0, c0 = p
    for rad in range(0, 40):
        for dr in range(-rad, rad+1):
            for dc in range(-rad, rad+1):
                r, c = r0+dr, c0+dc
                if 0 <= r < Hc and 0 <= c < Wc and np.isfinite(mult[r, c]):
                    return (r, c)
    raise SystemExit("no start/end water found")
SRC = nearest_ok(SRC); DST = nearest_ok(DST)

# Dijkstra, 8-connected, km-weighted steps
dist = {SRC: 0.0}; prev = {}
pq = [(0.0, SRC)]
kmlat = 111.0/DPD
while pq:
    du, u = heapq.heappop(pq)
    if u == DST: break
    if du > dist.get(u, np.inf): continue
    r, c = u
    kmlon = kmlat*math.cos(math.radians(LAT1 - r/DPD))
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0: continue
            v = (r+dr, c+dc)
            if not (0 <= v[0] < Hc and 0 <= v[1] < Wc): continue
            m = mult[v]
            if not np.isfinite(m): continue
            step = math.hypot(dr*kmlat, dc*kmlon)
            nd = du + step*0.5*(m + (mult[u] if np.isfinite(mult[u]) else m))
            if nd < dist.get(v, np.inf):
                dist[v] = nd; prev[v] = u
                heapq.heappush(pq, (nd, v))
if DST not in dist: raise SystemExit("NO PATH")
path = [DST]
while path[-1] != SRC: path.append(prev[path[-1]])
path.reverse()
pts = [(LON0 + c/DPD, LAT1 - r/DPD) for r, c in path]
km = 0.0; segs = []
for (a,b),(c2,d2) in zip(pts[:-1], pts[1:]):
    km += math.hypot((c2-a)*111*math.cos(math.radians((b+d2)/2)), (d2-b)*111)
stats = dict(length_km=round(km), cells=len(path),
             frac_surveyed=round(float(np.mean([knw[p] for p in path])), 3),
             frac_nodata=round(float(np.mean([not have[p] for p in path])), 3),
             mean_sigma=round(float(np.nanmean([sig[p] for p in path if np.isfinite(sig[p])])), 1),
             min_depth_on_path=round(float(np.nanmin([dep[p] for p in path if np.isfinite(dep[p])])), 1),
             shallowest_on_path=round(float(np.nanmax([dep[p] for p in path if np.isfinite(dep[p])])), 1))
json.dump(dict(stats=stats, path=[(round(lo,3), round(la,3)) for lo, la in pts]),
          open("corridor_found.json", "w"))
print("FOUND:", stats)

# render: found channel vs naive hand route
NAIVE = [(-94.19,58.77),(-92.0,59.6),(-88.5,60.8),(-84.0,62.2),(-80.5,62.9),
         (-74.5,62.6),(-68.5,61.9),(-64.5,60.9),(-60.0,59.3),(-56.5,57.5)]
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(20, 12.4), dpi=130)
fig.patch.set_facecolor("#04060c"); ax.set_facecolor("#04060c"); ax.set_axis_off()
ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1); ax.set_position([0.0, 0.09, 1.0, 0.84])
ext = [LON0, LON1, LAT0, LAT1]
water = np.zeros((Hc, Wc, 4)); water[...,0:3] = (0.024,0.039,0.078); water[...,3] = 1
ax.imshow(water, extent=ext, origin="upper", aspect=2.3, zorder=0)
lrgb = np.zeros((Hc, Wc, 4)); lrgb[...,0:3] = 0.13; lrgb[...,3] = np.where(land,1,0)
ax.imshow(lrgb, extent=ext, origin="upper", aspect=2.3, zorder=1)
risk = np.where(np.isfinite(mult), np.clip((mult-1)/14, 0, 1), np.nan)
rr2 = plt.cm.RdYlGn_r(risk); rr2[...,3] = np.where(np.isfinite(risk) & ~land, 0.75, 0)
ax.imshow(rr2, extent=ext, origin="upper", aspect=2.3, zorder=2)
xs, ys = zip(*NAIVE)
ax.plot(xs, ys, color="#8fa0c0", lw=1.6, ls=(0,(4,4)), alpha=0.8, zorder=5, label="straight-line route")
px, py = zip(*pts)
ax.plot(px, py, color="#5df0ff", lw=2.8, zorder=6, label="SeabedNet least-risk channel")
ax.scatter(-94.19, 58.77, s=200, marker="*", color="#ffd24d", edgecolor="k", zorder=8)
ax.annotate("PORT OF CHURCHILL", (-94.19, 58.77), xytext=(8,-16), textcoords="offset points",
            color="#ffd24d", fontsize=11, weight="bold")
leg = ax.legend(loc="upper right", frameon=False, fontsize=12)
for t in leg.get_texts(): t.set_color("#d8e0ee")
ax.set_title("THE CORRIDOR, FOUND — least-risk channel through completed depth + uncertainty  "
             "(green: easy water · red: shallow/uncertain/unknown)",
             color="white", fontsize=15.5, weight="bold", loc="left", pad=12)
fig.text(0.02, 0.05, f"{stats['length_km']:,} km · shallowest water on channel {abs(stats['shallowest_on_path']):.0f} m · "
         f"mean σ on channel {stats['mean_sigma']:.1f} m · {stats['frac_nodata']*100:.0f}% of track crosses no-data water",
         color="#cfd8ea", fontsize=11)
fig.text(0.02, 0.02, "cost = distance × (shallow <50 m penalty + σ/8 + no-data ×13); <20 m and land impassable · "
         "SeabedNet v5 · planning prior — NOT for navigation", color="#66779a", fontsize=8.5)
fig.savefig("corridor_found.png", dpi=130, facecolor="#04060c", bbox_inches="tight")
print("CORRIDOR_FOUND_DONE")
