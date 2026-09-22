#!/usr/bin/env python3
"""Label set for an imagery shoal detector: every NONNA-10 cell shallower than 8 m that lies >= 1 km from land (GSHHG land mask from
map/water.bin is not per-cell; use the 100 m aux_out land raster of the parent block) and whose 500 m neighbourhood (known cells only)
has median depth deeper than 15 m -> offshore isolated shoal. Also counts safe offshore cells (> 20 m, >= 1 km from land) for negatives.
-> shoal_labels.csv (block, i, j, lat, lon, depth, surround_m)"""
import glob, os, math, numpy as np, csv
from scipy import ndimage as ndi
R = 6378137.0
AUX = {}
for pf in glob.glob("aux_out/*.npz"):
    b = np.load(pf, allow_pickle=True)["bbox3857"]; AUX[pf] = (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))
def parent_of(bb):   # aux_out block whose bbox contains this tile's centre
    cx, cy = (bb[0] + bb[2])/2, (bb[1] + bb[3])/2
    for pf, (x0, y0, x1, y1) in AUX.items():
        if x0 <= cx < x1 and y0 <= cy < y1: return pf
    return None
rows = []; n_blocks = 0; n_safe = 0; n_comp = 0
for f in sorted(glob.glob("tiles10/*.npz")):
    name = os.path.basename(f); a = np.load(f, allow_pickle=True); z = a["z"].astype("float32"); K = np.isfinite(z)
    pf = parent_of(a["bbox3857"])
    if pf is None: continue
    if K.sum() < 2000 or not (K & (z > -8)).any(): continue
    b = a["bbox3857"]; H, W = z.shape; x0, x1 = min(b[0], b[2]), max(b[0], b[2]); y0, y1 = min(b[1], b[3]), max(b[1], b[3])
    P = np.load(pf, allow_pickle=True); L = P["land"].astype("float32"); pb = P["bbox3857"]; px0, px1 = min(pb[0], pb[2]), max(pb[0], pb[2]); py0, py1 = min(pb[1], pb[3]), max(pb[1], pb[3])
    Lm = np.isfinite(L) & (L > 0.5); dland = ndi.distance_transform_edt(~Lm)*100.0 if Lm.any() else np.full(L.shape, 99999.0)
    # map each 10 m cell to the parent 100 m cell
    ii, jj = np.mgrid[0:H, 0:W]; X = x0 + (jj + 0.5)/W*(x1 - x0); Y = y1 - (ii + 0.5)/H*(y1 - y0)
    pj = ((X - px0)/(px1 - px0)*L.shape[1]).astype(int).clip(0, L.shape[1]-1); pi = ((py1 - Y)/(py1 - py0)*L.shape[0]).astype(int).clip(0, L.shape[0]-1)
    dl = dland[pi, pj]; off = dl >= 1000
    n_blocks += 1; n_safe += int((K & (z < -20) & off).sum())
    sh = K & (z > -8) & (z < 0) & off
    if not sh.any(): continue
    n_comp += int(ndi.label(ndi.binary_dilation(sh, iterations=5))[1])
    zz = np.where(K, z, np.nan)
    for i, j in np.argwhere(sh):
        w = zz[max(0, i-25):i+26, max(0, j-25):j+26]; v = w[np.isfinite(w)]
        if len(v) < 10: continue
        med = float(np.median(v))
        if med < -15:
            lon = math.degrees(X[i, j]/R); lat = math.degrees(2*math.atan(math.exp(Y[i, j]/R)) - math.pi/2)
            rows.append((name[:-4], int(i), int(j), round(lat, 5), round(lon, 5), round(float(z[i, j]), 1), round(med, 1), int(dl[i, j])))
with open("shoal_labels.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["block", "i", "j", "lat", "lon", "depth_m", "surround_m", "dist_land_m"]); w.writerows(rows)
print("LABELS_DONE blocks", n_blocks, "offshore isolated shoal cells", len(rows), "in", len(set(r[0] for r in rows)), "blocks | distinct offshore shallow features (<8 m, dilated 50 m)", n_comp, "| safe offshore cells", n_safe)
