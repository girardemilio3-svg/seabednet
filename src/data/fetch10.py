import numpy as np, tifffile, requests, io, time, os
a=tifffile.imread("footprint10.tif").astype("float32")
a[np.abs(a)>1e30]=np.nan; a[a==0]=np.nan
G=a.shape[0]
X0,Y0=-2.002629999514532e7,-2.0048889618972085e7
X1,Y1= 2.002660557456404e7, 2.0049195543083742e7
px=(X1-X0)/G; py=(Y1-Y0)/G
valid=np.isfinite(a)
B=4                                    # 4x4 footprint cells ≈ 2500x2500 native 10m px
blocks=[(r,c) for r in range(G//B) for c in range(G//B)
        if valid[r*B:(r+1)*B, c*B:(c+1)*B].any()]
print(f"{len(blocks)} candidate 10m blocks")
BASE="https://nonna-geoserver.data.chs-shc.ca/geoserver/wcs"
got=fail=0
for n,(r,c) in enumerate(blocks):
    fn=f"tiles10/b{r:04d}_{c:04d}.npz"
    if os.path.exists(fn): got+=1; continue
    ymax=Y1-r*B*py; ymin=Y1-(r+1)*B*py
    xmin=X0+c*B*px; xmax=X0+(c+1)*B*px
    p={"service":"WCS","version":"2.0.1","request":"GetCoverage",
       "coverageId":"nonna__NONNA 10 Coverage","format":"image/geotiff",
       "subset":[f"x({xmin},{xmax})",f"y({ymin},{ymax})"]}
    try:
        rq=requests.get(BASE,params=p,timeout=240)
        if rq.status_code==200 and "xml" not in rq.headers.get("Content-Type",""):
            z=tifffile.imread(io.BytesIO(rq.content)).astype("float32")
            z[np.abs(z)>1e30]=np.nan; z[z==0]=np.nan; z[z>25]=np.nan
            if np.isfinite(z).mean()>0.002:
                np.savez_compressed(fn,z=z.astype("float16"),bbox3857=[xmin,ymin,xmax,ymax])
                got+=1
            else: fail+=1
        else: fail+=1
    except Exception: fail+=1
    if (n+1)%200==0: print(f"[{n+1}/{len(blocks)}] saved={got} empty/fail={fail}",flush=True)
    time.sleep(0.25)
print(f"FETCH10_DONE saved={got} fail={fail}")
