#!/usr/bin/env python3
"""Distance-stratified held-out eval: v5 vs gravity prior, binned by distance
to the nearest VISIBLE sounding. This is the anti-leakage analysis: the gravity
prior ingests ship soundings, so it looks good near them; the claim that
matters is who wins far from any sounding (the Churchill regime).

Usage: V5_SIZE=small python3 stratified_eval.py   (needs v5_<size>.pt)
Bins are in km, using each patch's native resolution for pixel->metre.
"""
import os, numpy as np, torch
from scipy.ndimage import distance_transform_edt
from v5_data import Corpus
from v5_model import V5, normalize

DEV = "cuda"
SIZE = os.environ.get("V5_SIZE", "small")
N_PATCH = int(os.environ.get("N_PATCH", "80"))
P = 256
BINS_KM = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 1e9]
torch.manual_seed(0)

torch.zeros(8, device=DEV)
corpus = Corpus(P=P)
net = V5(SIZE).to(DEV)
ck = torch.load(f"v5_{SIZE}.pt", map_location=DEV, weights_only=False)
net.load_state_dict(ck["net"]); net.eval()
print(f"v5-{SIZE} @ step {ck['step']}, {N_PATCH} holdout patches, center-masked")

rng = np.random.default_rng(0)
acc = {i: {"v5": [], "grav": [], "n": 0} for i in range(len(BINS_KM)-1)}
used = 0
with torch.no_grad():
    while used < N_PATCH:
        s = corpus.sample(min_valid=0.9, holdout=True)
        if s is None: continue
        m = np.ones((P, P), np.float32); h = int(P*0.6); i0 = (P-h)//2
        m[i0:i0+h, i0:i0+h] = 0
        known, depth, grav = s["known"], s["depth"], s["gravity"]
        mvis = known*m
        hid = (known*(1-m)) > 0
        if hid.sum() < 300: continue
        t = lambda a: torch.tensor(a)[None, None].float().to(DEV)
        dn, gn, mu0, sd0 = normalize(t(depth), t(mvis), t(grav))
        ridx = torch.tensor([1 if s["res_m"] == 10.0 else 0], device=DEV)
        mu, lv = net(torch.cat([dn*t(mvis), t(mvis), gn], 1), ridx)
        if os.environ.get("V5_RESIDUAL", "0") == "1": mu = mu.float() + gn.float()
        est = (mu.float()*sd0 + mu0)[0, 0].cpu().numpy()
        # distance (km) from each hidden pixel to nearest visible sounding
        dist_px = distance_transform_edt(mvis < 0.5)
        dist_km = dist_px * s["res_m"] / 1000.0
        ev5 = np.abs(est - depth); eg = np.abs(grav - depth)
        for b in range(len(BINS_KM)-1):
            sel = hid & (dist_km >= BINS_KM[b]) & (dist_km < BINS_KM[b+1])
            if sel.sum() < 30: continue
            acc[b]["v5"].append(ev5[sel]); acc[b]["grav"].append(eg[sel])
            acc[b]["n"] += int(sel.sum())
        used += 1

print(f"\n===== DISTANCE-STRATIFIED HELD-OUT (v5-{SIZE} vs gravity prior) =====")
print(f"{'dist to sounding':>18} {'pixels':>9} {'v5 MAE':>9} {'gravity MAE':>12} {'v5 wins by':>11}")
for b in range(len(BINS_KM)-1):
    if not acc[b]["v5"]: continue
    v = np.concatenate(acc[b]["v5"]); g = np.concatenate(acc[b]["grav"])
    lo, hi = BINS_KM[b], BINS_KM[b+1]
    lab = f"{lo:g}-{hi:g} km" if hi < 1e8 else f">{lo:g} km"
    print(f"{lab:>18} {acc[b]['n']:>9} {v.mean():>8.2f}m {g.mean():>11.2f}m {100*(g.mean()-v.mean())/g.mean():>+10.1f}%")
print("STRAT_DONE")
