#!/usr/bin/env python3
"""Cut the Canada window from SRTM15+ (gravity-predicted global bathymetry)
into a compact npz used as v5's physics-prior conditioning channel."""
import numpy as np, netCDF4
LON0, LON1, LAT0, LAT1 = -142.0, -50.0, 40.0, 84.0
ds = netCDF4.Dataset("planetary/SRTM15_V2.7.nc")
print({k: ds.variables[k].shape for k in ds.variables})
lon = ds.variables["lon"][:]; lat = ds.variables["lat"][:]
i0, i1 = np.searchsorted(lon, [LON0, LON1])
j0, j1 = np.searchsorted(lat, [LAT0, LAT1])
z = ds.variables["z"][j0:j1, i0:i1].astype("float32")
print("canada window", z.shape, "depth", np.nanmin(z), "..", np.nanmax(z))
np.savez_compressed("planetary/gravity_prior_canada.npz",
                    z=z.astype("float16"),
                    lon=[float(lon[i0]), float(lon[i1-1])],
                    lat=[float(lat[j0]), float(lat[j1-1])])
print("GRAVITY_PRIOR_DONE")
