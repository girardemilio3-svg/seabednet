"""Stable per-checkpoint tracker: 6 fixed held-out patches, EMA vs raw weights."""
import math, numpy as np, torch
from diffusion_model import UNet
import sample_v2 as sv

ck = torch.load("seabednet_v2.pt", map_location="cuda")
print(f"step {ck['step']}")
rng = np.random.default_rng(99)
patches = []
while len(patches) < 6:
    name = sv.HOLDOUT[rng.integers(3)]
    z = np.load(f"tiles/{name}.npz", allow_pickle=True)["z"]; z[z > 25] = np.nan
    if z.shape[0] < sv.P or z.shape[1] < sv.P: continue
    i, j = rng.integers(z.shape[0]-sv.P), rng.integers(z.shape[1]-sv.P)
    p = z[i:i+sv.P, j:j+sv.P]
    if np.isfinite(p).mean() > 0.95 and np.nanstd(p) > 15:
        patches.append((name, p))

for wname in ["ema", "net"]:
    sv.net.load_state_dict(ck[wname]); sv.net.eval()
    maes = []
    for name, p in patches:
        known = np.isfinite(p).astype(np.float32)
        m = sv.block_mask(0.6)*known
        hid = known*(1-m)
        torch.manual_seed(0)
        mean, _ = sv.ddim_repaint(torch.tensor(np.nan_to_num(p/sv.SCALE)*m)[None,None].float().cuda(),
                                  torch.tensor(m)[None,None].float().cuda(),
                                  n_steps=30, n_samples=4)
        maes.append(np.abs(mean*sv.SCALE-p)[hid > 0].mean())
    print(f"  {wname:4s}: MAE {np.mean(maes):7.1f} m   per-patch {[f'{x:.0f}' for x in maes]}")
