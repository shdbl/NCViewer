"""生成 CMIP6 风格的 360_day 海冰密集度演示文件。"""
from pathlib import Path
import numpy as np
import xarray as xr
import cftime

root = Path(__file__).resolve().parents[1]
out = root / "data" / "demo_siconc.nc"
lat = np.arange(-90, 91, 2, dtype=float)
lon = np.arange(0, 360, 2, dtype=float)
time = xr.cftime_range("2015-01-01", periods=12, freq="MS", calendar="360_day")
month = np.arange(12)[:, None, None]
la = np.deg2rad(lat)[None, :, None]; lo = np.deg2rad(lon)[None, None, :]
season = 8 * np.cos(2 * np.pi * month / 12)
field = np.clip(50 + 45 * (np.abs(np.sin(la)) ** 2) + season * (0.3 + 0.7 * np.abs(np.sin(la))) + 3 * np.cos(lo), 0, 100)
da = xr.DataArray(field.astype("float32"), dims=("time", "lat", "lon"), coords={"time": time, "lat": lat, "lon": lon}, name="siconc")
da.attrs.update(units="%", long_name="sea_ice_area_fraction", missing_value=-9999.0)
ds = da.to_dataset(); ds.attrs["calendar"] = "360_day"
ds.to_netcdf(out, encoding={"siconc": {"_FillValue": -9999.0}})
print(f"已生成：{out}")