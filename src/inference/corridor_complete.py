#!/usr/bin/env python3
"""Churchill Corridor Atlas: complete the corridor blocks with v5-small.

Windowed inference (P=256, stride 128, hann blend), gravity channel sampled
per block, batched forward passes in bf16. Provenance discipline matches the
v3 national run: windows need >=400 known px; predicted land (z > -4 m) is
masked out. Output: corridor_out/<block>.npz (complete, sigma, known, bbox3857).
"""
import glob, math, os, numpy as np, torch
from scipy import ndimage as ndi
from v5_data import GravityPrior, lat_of_y, lon_of_x
from v5_model import V5, normalize

DEV = "cuda"; P = 256; S = 128; BW = 16   # window batch
net = V5("small").to(DEV)
ck = torch.load("v5_small.pt", map_location=DEV, weights_only=False)
net.load_state_dict(ck["net"]); net.eval()
grav = GravityPrior()
os.makedirs("corridor_out", exist_ok=True)
files = [l.strip() for l in open("corridor_blocks.txt") if l.strip()]
print(f"v5-small @ {ck['step']} — {len(files)} corridor blocks")

win = np.outer(np.hanning(P), np.hanning(P)) + 1e-3
for n, f in enumerate(files):
    out = f.replace("tiles_nat", "corridor_out")
    if os.path.exists(out): continue
    d = np.load(f, allow_pickle=True)
    z = d["z"].astype("float32"); bbox = d["bbox3857"]
    H, W = z.shape
    known = np.isfinite(z).astype(np.float32)
    if known.sum() < 500: continue
    x0, y0, x1, y1 = bbox
    lons = np.array([lon_of_x(x) for x in np.linspace(min(x0,x1), max(x0,x1), W)])
    lats = np.array([lat_of_y(y) for y in np.linspace(max(y0,y1), min(y0,y1), H)])
    G = grav.sample(np.tile(lons, (H,1)), np.tile(lats[:,None], (1,W))).astype("float32")
    Hp = (H//S+3)*S; Wp = (W//S+3)*S
    zp = np.full((Hp,Wp), np.nan, np.float32); zp[:H,:W] = z
    kp = np.zeros((Hp,Wp), np.float32); kp[:H,:W] = known
    gp = np.zeros((Hp,Wp), np.float32); gp[:H,:W] = G
    gp[H:,:] = G[-1:,:].mean(); gp[:,W:] = gp[:,W-1:W]
    accm = np.zeros((Hp,Wp)); accs = np.zeros((Hp,Wp)); wacc = np.zeros((Hp,Wp))
    coords = [(i,j) for i in range(0,Hp-P+1,S) for j in range(0,Wp-P+1,S)
              if kp[i:i+P,j:j+P].sum() >= 400]
    with torch.no_grad():
        for b0 in range(0, len(coords), BW):
            cb = coords[b0:b0+BW]
            zb = np.stack([np.nan_to_num(zp[i:i+P,j:j+P]) for i,j in cb])
            kb = np.stack([kp[i:i+P,j:j+P] for i,j in cb])
            gb = np.stack([gp[i:i+P,j:j+P] for i,j in cb])
            t = lambda a: torch.tensor(a)[:,None].float().to(DEV)
            dt, kt, gt = t(zb), t(kb), t(gb)
            dn, gn, mu0, sd0 = normalize(dt, kt, gt)
            ridx = torch.zeros(len(cb), device=DEV, dtype=torch.long)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                mu, lv = net(torch.cat([dn*kt, kt, gn], 1), ridx)
            est = (mu.float()*sd0 + mu0)[:,0].cpu().numpy()
            sig = (torch.exp(0.5*lv.float())*sd0)[:,0].cpu().numpy()
            for q,(i,j) in enumerate(cb):
                accm[i:i+P,j:j+P] += est[q]*win
                accs[i:i+P,j:j+P] += sig[q]*win
                wacc[i:i+P,j:j+P] += win
    est = np.where(wacc>0, accm/np.maximum(wacc,1e-6), np.nan)[:H,:W]
    sig = np.where(wacc>0, accs/np.maximum(wacc,1e-6), np.nan)[:H,:W]
    complete = np.where(known>0, z, est)
    complete[(known==0)&(complete>-4)] = np.nan
    filled = np.isfinite(complete)&(known==0)
    np.savez_compressed(out, complete=complete.astype("float16"),
                        sigma=np.where(filled, np.nan_to_num(sig), 0).astype("float16"),
                        known=known.astype(bool), bbox3857=bbox)
    print(f"[{n+1}/{len(files)}] {os.path.basename(f)}  windows={len(coords)}", flush=True)
print("CORRIDOR_COMPLETE_DONE")
