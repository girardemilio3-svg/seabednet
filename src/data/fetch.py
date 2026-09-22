import math, requests, tifffile, numpy as np

R=6378137.0
def to3857(lon,lat):
    x=R*math.radians(lon)
    y=R*math.log(math.tan(math.pi/4+math.radians(lat)/2))
    return x,y

# St. Anns Bank area, E of Cape Breton, NS
lon0,lat0,lon1,lat1 = -59.55,46.05,-58.75,46.65
xmin,ymin=to3857(lon0,lat0); xmax,ymax=to3857(lon1,lat1)
BASE="https://nonna-geoserver.data.chs-shc.ca/geoserver/wcs"
def get(cov,fn):
    p={"service":"WCS","version":"2.0.1","request":"GetCoverage",
       "coverageId":cov,"format":"image/geotiff",
       "subset":[f"x({xmin},{xmax})",f"y({ymin},{ymax})"]}
    r=requests.get(BASE,params=p,timeout=120)
    print(cov,"->",r.status_code,"bytes",len(r.content),r.headers.get("Content-Type"))
    if r.status_code==200 and "xml" not in r.headers.get("Content-Type",""):
        open(fn,"wb").write(r.content); return fn
    open(fn+".err.xml","wb").write(r.content); print("  ",r.content[:300]); return None

f=get("nonna__NONNA 100 Coverage","stanns_100.tif")
if f:
    a=tifffile.imread(f).astype("float32")
    print("shape",a.shape,"dtype",a.dtype)
    print("min",np.nanmin(a),"max",np.nanmax(a))
    u,c=np.unique(a[np.isfinite(a)],return_counts=True)
    print("most common vals:",sorted(zip(c,u),reverse=True)[:5])
