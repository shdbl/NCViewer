"""从真实 NSIDC CDR v6 数据生成 demo_siconc.nc。

- 数据源：D:\\data\\BJHB\\SIC_NSIDC_CDR_v6_daily_EASE25_nn_1979-2024.nc
  （NOAA/NSIDC Climate Data Record of Passive Microwave Sea Ice Concentration，
   EASE-Grid 2.0 North，EPSG:3408，25km，361×361）
- 截取：2024 年每月 15 日（12 时次），保留 EASE 全网格、2D 辅助 lat/lon、crs
- 保留 grid_mapping / 2D 辅助坐标：NCViewer 自动识别为曲线网格地图 + 自动北极极射投影，
  且能展示时间滑块看海冰季节变化
"""
from pathlib import Path
import numpy as np
import xarray as xr

root = Path(__file__).resolve().parents[1]
src = r"D:\data\BJHB\SIC_NSIDC_CDR_v6_daily_EASE25_nn_1979-2024.nc"
out = root / "data" / "demo_siconc.nc"

ds = xr.open_dataset(src)
sic = ds["sic"]  # (time, y, x)

# 取 2024 年每月 15 日
dates = []
for m in range(1, 13):
    day = f"2024-{m:02d}-15"
    # 从时间坐标精确匹配（每日数据都有）
    dates.append(np.datetime64(day))
demo = sic.sel(time=dates)
print(f"截取 {len(dates)} 时次：{str(demo.time.values[0])[:10]} ~ {str(demo.time.values[-1])[:10]}")
print(f"shape {demo.shape}，{demo.nbytes / 1e6:.1f} MB")

d = demo.to_dataset(name="sic")
# 保留 2D 辅助经纬度坐标 + crs（grid_mapping）
d = d.assign_coords(lat=ds["lat"], lon=ds["lon"])
# crs 是网格映射变量（grid_mapping_name=lambert_azimuthal_equal_area，EPSG:3408）
d["crs"] = ds["crs"]
d["crs"].attrs = ds["crs"].attrs
d = d.set_coords("crs")
d["sic"].attrs = {
    "long_name": "sea_ice_area_fraction",
    "standard_name": "sea_ice_area_fraction",
    "units": "1",
    "grid_mapping": "crs",
    "missing_value": np.nan,
}
d.attrs = {
    "title": "NSIDC CDR v6 sea ice concentration (demo subset, 2024 monthly mid-month)",
    "source": "NOAA/NSIDC Climate Data Record of Passive Microwave Sea Ice Concentration",
    "grid": "EASE-Grid 2.0 North, EPSG:3408, 361x361, R=6371228 m",
    "References": "https://nsidc.org/data/nsidc-0532",
    "Conventions": "CF-1.8",
}
d.to_netcdf(out, encoding={"sic": {"dtype": "float32", "zlib": True, "complevel": 4, "_FillValue": np.nan}})
print(f"已生成：{out}（{out.stat().st_size / 1e6:.1f} MB）")
