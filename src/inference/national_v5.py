#!/usr/bin/env python3
"""CANADA COMPLETE: all 437 national blocks with v5-small.

Windowed inference (P=256, stride 128, hann blend), gravity channel sampled
per block, batched forward passes in bf16. Provenance discipline matches the
v3 national run: windows need >=400 known px; predicted land (z > -4 m) is
masked out. Output: national_v5_out/<block>.npz (complete, sigma, known, bbox3857).
"""
import glob, math, os, numpy as np, torch
from scipy import ndimage as ndi
from v5_data import GravityPrior, lat_of_y, lon_of_x
from v5_model import V5, normalize


def tta_folds(n):   # 1: identity; 4: the four flips; 8: all rotations x flips
    return [(0, False)] if n <= 1 else ([(0, False), (0, True), (2, False), (2, True)] if n == 4 else [(k, fl) for k in range(4) for fl in (False, True)])
def tta_forward(net, xin, ridx, n):
    mus, lvs = [], []
    for k, fl in tta_folds(n):
        xa = torch.rot90(xin, k, (2, 3)); xa = torch.flip(xa, (3,)) if fl else xa
        m_, l_ = net(xa, ridx); m_ = torch.flip(m_, (3,)) if fl else m_; l_ = torch.flip(l_, (3,)) if fl else l_
        mus.append(torch.rot90(m_, -k, (2, 3))); lvs.append(torch.rot90(l_, -k, (2, 3)))
    if n <= 1: return mus[0], lvs[0]
    return torch.stack(mus).float().mean(0), torch.log(torch.stack(lvs).float().exp().mean(0))

DEV = "cuda"; P = 256; S = 128; BW = int(os.environ.get("V5_BW", "16")); TTA = int(os.environ.get("V5_TTA", "0"))   # window batch; test-time augmentation folds
CKPT = os.environ.get("V5_CKPT", "v5_small.pt"); OUTD = os.environ.get("V5_OUT", "national_v5_out"); S1 = os.environ.get("V5_S1", "0") == "1"
net = V5("small", in_ch=3 + (3 if S1 else 0)).to(DEV)
ck = torch.load(CKPT, map_location=DEV, weights_only=False)
net.load_state_dict(ck["net"]); net.eval()
grav = GravityPrior()
os.makedirs(OUTD, exist_ok=True)
files = sorted(glob.glob("tiles_nat/*.npz"))
print(f"v5-small @ {ck['step']} — {len(files)} corridor blocks")

win = np.outer(np.hanning(P), np.hanning(P)) + 1e-3
for n, f in enumerate(files):
    out = f.replace("tiles_nat", OUTD)
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
    ap = np.zeros((3, Hp, Wp), np.float32)
    if S1:
        sp = f"aux_s1/{os.path.basename(f)}"
        if os.path.exists(sp):
            b = np.load(sp); v = b["vv"].astype(np.float32); h = b["vh"].astype(np.float32); m = np.isfinite(v)
            ap[0, :H, :W] = np.where(m, (v + 20.0)/20.0, 0.0); ap[1, :H, :W] = np.where(np.isfinite(h), (h + 30.0)/20.0, 0.0); ap[2, :H, :W] = m
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
            at = torch.tensor(np.stack([ap[:, i:i+P, j:j+P] for i, j in cb])).float().to(DEV)
            dn, gn, mu0, sd0 = normalize(dt, kt, gt)
            ridx = torch.zeros(len(cb), device=DEV, dtype=torch.long)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                mu, lv = tta_forward(net, torch.cat([dn*kt, kt, gn] + ([at] if S1 else []), 1), ridx, TTA)
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
