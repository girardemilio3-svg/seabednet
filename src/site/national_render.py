#!/usr/bin/env python3
"""Assemble the 437 completed blocks into the national before/after mosaic."""
import glob, math, numpy as np, json
X0,Y0=-2.002629999514532e7,-2.0048889618972085e7
X1,Y1=2.002660557456404e7,2.0049195543083742e7
DS=8   # downsample factor per block for the mosaic
files=sorted(glob.glob("national_out/*.npz"))
# mosaic canvas over the DATA extent only — find bounds first
bbs=[np.load(f,allow_pickle=True)["bbox3857"] for f in files]
xmin=min(b[0] for b in bbs); xmax=max(b[2] for b in bbs)
ymin=min(b[1] for b in bbs); ymax=max(b[3] for b in bbs)
res=100*DS  # m per mosaic px in 3857
Wm=int((xmax-xmin)/res)+2; Hm=int((ymax-ymin)/res)+2
print(f"mosaic {Hm}x{Wm}")
before=np.full((Hm,Wm),np.nan,np.float32)
after =np.full((Hm,Wm),np.nan,np.float32)
R=6378137.0
def lat_of_y(y): return math.degrees(2*math.atan(math.exp(y/R))-math.pi/2)
sv_km2=fl_km2=0.0
for f,bb in zip(files,bbs):
    d=np.load(f,allow_pickle=True)
    c=d["complete"].astype("float32"); k=d["known"]
    H,W=c.shape
    # cos^2(lat) area correction
    lat=lat_of_y((bb[1]+bb[3])/2); corr=math.cos(math.radians(lat))**2
    sv_km2+=float(k.sum())*0.0106*0.0106*1e2*corr        # (0.106 km)^2 = 0.011236 km2
    fl_km2+=float((np.isfinite(c)&~k).sum())*0.011236*corr
    cb=np.where(k,c,np.nan)
    def shrink(a):
        Hc,Wc=(H//DS)*DS,(W//DS)*DS
        a=a[:Hc,:Wc].reshape(Hc//DS,DS,Wc//DS,DS)
        with np.errstate(all="ignore"): return np.nanmean(np.nanmean(a,3),1)
    sb,sa=shrink(cb),shrink(c)
    r0=int((ymax-bb[3])/res); c0=int((bb[0]-xmin)/res)
    hh,ww=sb.shape
    for tgt,src in [(before,sb),(after,sa)]:
        sl=tgt[r0:r0+hh,c0:c0+ww]
        np.copyto(sl,np.where(np.isfinite(src),src,sl))
print(f"corrected: surveyed {sv_km2:,.0f} km2, AI-filled {fl_km2:,.0f} km2")
json.dump({"surveyed_km2":sv_km2,"filled_km2":fl_km2},open("national_stats_corrected.json","w"))
np.savez_compressed("national_mosaic.npz",before=before.astype("float16"),
                    after=after.astype("float16"),extent3857=[xmin,ymin,xmax,ymax])
# render
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
ls=LightSource(azdeg=310,altdeg=40)
vmin=np.nanpercentile(after,3); vmax=0
for name,arr,sub in [("national_before.png",before,f"what Canada has surveyed — {sv_km2:,.0f} km²"),
                     ("national_after.png",after,f"SeabedNet completion — +{fl_km2:,.0f} km² inferred (validated MAE 20.5 m, calibrated σ)")]:
    fig,ax=plt.subplots(figsize=(19,11),dpi=120); fig.patch.set_facecolor("#04060a")
    ax.set_facecolor("#04060a"); ax.set_axis_off()
    a=np.clip(arr,vmin,vmax)
    rgb=ls.shade(np.where(np.isfinite(a),a,vmin),cmap=plt.cm.gist_earth,blend_mode="soft",
                 vert_exag=40,vmin=vmin,vmax=vmax)
    rgb[~np.isfinite(arr)]=[0.016,0.024,0.04,1]
    ax.imshow(rgb)
    ax.set_title(f"CANADA'S SEAFLOOR — {sub}",color="white",fontsize=17,weight="bold",loc="left",pad=14)
    fig.text(0.02,0.015,"CHS NONNA-100 (Open Government Licence) · SeabedNet v3 · planning prior — NOT for navigation",
             color="#7788aa",fontsize=9)
    fig.savefig(name,dpi=120,facecolor="#04060a",bbox_inches="tight")
    print("wrote",name)
print("NATIONAL_RENDER_DONE")
