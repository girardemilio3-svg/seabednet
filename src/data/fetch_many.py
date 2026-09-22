import math, requests, tifffile, numpy as np, io, time
R=6378137.0
def to3857(lon,lat): return R*math.radians(lon), R*math.log(math.tan(math.pi/4+math.radians(lat)/2))
REGIONS={
 "fundy":(-66.4,44.9,-65.4,45.5),"german_bank":(-66.7,43.0,-65.7,43.7),
 "halifax":(-63.9,44.2,-62.9,44.8),"sable":(-60.5,43.7,-59.5,44.3),
 "laurentian":(-60.0,47.2,-59.0,47.9),"estuary":(-69.5,48.0,-68.5,48.7),
 "chaleur":(-66.0,47.8,-65.0,48.3),"georgia":(-123.8,48.9,-122.9,49.5),
 "juandefuca":(-124.5,48.2,-123.5,48.6),"hecate":(-131.5,53.0,-130.5,53.8),
 "placentia":(-54.6,47.0,-53.8,47.7),"grandbanks":(-52.0,46.0,-51.0,46.8),
 "northumberland":(-64.0,45.8,-63.0,46.3),"lancaster":(-84.0,74.0,-82.5,74.5),
}
BASE="https://nonna-geoserver.data.chs-shc.ca/geoserver/wcs"
for name,(a,b,c,dd) in REGIONS.items():
    xmin,ymin=to3857(a,b); xmax,ymax=to3857(c,dd)
    p={"service":"WCS","version":"2.0.1","request":"GetCoverage","coverageId":"nonna__NONNA 100 Coverage",
       "format":"image/geotiff","subset":[f"x({xmin},{xmax})",f"y({ymin},{ymax})"]}
    try:
        r=requests.get(BASE,params=p,timeout=180)
        if r.status_code==200 and "xml" not in r.headers.get("Content-Type",""):
            z=tifffile.imread(io.BytesIO(r.content)).astype("float32")
            z[z>1e30]=np.nan; z[z==0]=np.nan
            vf=float(np.isfinite(z).mean())
            np.savez_compressed(f"tiles/{name}.npz",z=z,bbox=[a,b,c,dd])
            print(f"{name:16s} {z.shape} valid={vf*100:5.1f}%  depth {np.nanmin(z):7.0f}..{np.nanmax(z):5.0f}")
        else:
            print(f"{name:16s} FAIL {r.status_code} {r.content[:120]}")
    except Exception as e:
        print(f"{name:16s} ERR {e}")
    time.sleep(1.5)
print("done")
