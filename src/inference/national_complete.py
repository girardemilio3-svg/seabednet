#!/usr/bin/env python3
"""Complete every surveyed block of Canada's NONNA-100 archive with v3."""
import glob, os, numpy as np, torch, json
from scipy import ndimage as ndi
from v3_model import NetV3
DEV="cuda"; P=192; S=96
net=NetV3().to(DEV); net.load_state_dict(torch.load("v3.pt",map_location=DEV)); net.eval()
temp=float(np.load("v3_calib.npz")["temperature"])
os.makedirs("national_out",exist_ok=True)
files=sorted(glob.glob("tiles_nat/*.npz"))
stats={"blocks":0,"surveyed_km2":0.0,"filled_km2":0.0}
cell=0.106  # km approx at mid-lat; refined per-block by lat would be better; acceptable for v0 stats
for n,f in enumerate(files):
    out=f.replace("tiles_nat","national_out")
    if os.path.exists(out): continue
    d=np.load(f,allow_pickle=True)
    z=d["z"].astype("float32"); bbox=d["bbox3857"]
    H,W=z.shape
    known=np.isfinite(z).astype(np.float32)
    if known.sum()<500:
        continue
    Hp=(H//S+3)*S; Wp=(W//S+3)*S
    zp=np.full((Hp,Wp),np.nan,np.float32); zp[:H,:W]=z
    kp=np.zeros((Hp,Wp),np.float32); kp[:H,:W]=known
    accم=np.zeros((Hp,Wp)); accs=np.zeros((Hp,Wp)); wacc=np.zeros((Hp,Wp))
    win=np.outer(np.hanning(P),np.hanning(P))+1e-3
    with torch.no_grad():
        for i in range(0,Hp-P+1,S):
            for j in range(0,Wp-P+1,S):
                kw=kp[i:i+P,j:j+P]
                if kw.sum()<400: continue
                zw=zp[i:i+P,j:j+P]
                mu0,sd0=np.nanmean(zw),np.nanstd(zw)+1e-3
                zn=np.nan_to_num((zw-mu0)/sd0)
                mu,lv=net(torch.tensor(zn*kw)[None,None].float().to(DEV),
                          torch.tensor(kw)[None,None].float().to(DEV))
                est=mu[0,0].cpu().numpy()*sd0+mu0
                sig=np.exp(0.5*lv[0,0].cpu().numpy())*sd0*temp
                accم[i:i+P,j:j+P]+=est*win; accs[i:i+P,j:j+P]+=sig*win; wacc[i:i+P,j:j+P]+=win
    est=np.where(wacc>0,accم/np.maximum(wacc,1e-6),np.nan)[:H,:W]
    sig=np.where(wacc>0,accs/np.maximum(wacc,1e-6),np.nan)[:H,:W]
    # destripe prior, keep real data
    es=ndi.gaussian_filter(np.nan_to_num(est,nan=0),2.0)
    ew=ndi.gaussian_filter(np.isfinite(est).astype(float),2.0)
    est_s=np.where(np.isfinite(est),es/np.maximum(ew,1e-6),np.nan)
    complete=np.where(known>0,z,est_s)
    complete[(known==0)&(complete>-4)]=np.nan          # predicted land
    filled=np.isfinite(complete)&(known==0)
    np.savez_compressed(out,complete=complete.astype("float16"),
                        sigma=np.where(filled,sig,0).astype("float16"),
                        known=known.astype(bool),bbox3857=bbox)
    stats["blocks"]+=1
    stats["surveyed_km2"]+=float(known.sum())*cell*cell
    stats["filled_km2"]+=float(filled.sum())*cell*cell
    if (n+1)%25==0:
        print(f"[{n+1}/{len(files)}] surveyed {stats['surveyed_km2']:,.0f} km2  filled {stats['filled_km2']:,.0f} km2",flush=True)
json.dump(stats,open("national_stats.json","w"),indent=1)
print(f"NATIONAL_COMPLETE_DONE {stats}")
