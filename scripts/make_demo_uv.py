"""从真实 NCEP Reanalysis 2 风场数据生成 demo_uv.nc（u/v 合一）。

- 数据源：D:\\data\\uwnd.mon.mean.nc + D:\\data\\vwnd.mon.mean.nc
  （NCEP/DOE AMIP-II Reanalysis，全球月平均风场，公共领域）
- 截取：最近 12 个月（2023-10 ~ 2024-09），850 hPa 层，全球 73×144 网格
- u、v 两个变量放同一文件：树里 Ctrl 多选 u+v → 合并绘图 → 自动矢量箭头图
"""
from pathlib import Path
import numpy as np
import xarray as xr

root = Path(__file__).resolve().parents[1]
u_src = r"D:\data\uwnd.mon.mean.nc"
v_src = r"D:\data\vwnd.mon.mean.nc"
out = root / "data" / "demo_uv.nc"

ds_u = xr.open_dataset(u_src)
ds_v = xr.open_dataset(v_src)

# 最近 12 个月 + 850 hPa
u = ds_u["uwnd"].isel(time=slice(-12, None)).sel(level=850)
v = ds_v["vwnd"].isel(time=slice(-12, None)).sel(level=850)
print(f"u: {u.shape} {str(u.time.values[0])[:10]} ~ {str(u.time.values[-1])[:10]} @ 850hPa")

d = xr.Dataset({"u": u, "v": v})
d["u"].attrs = {"long_name": "纬向风（u 分量）", "standard_name": "eastward_wind",
                "units": "m s-1", "missing_value": np.nan}
d["v"].attrs = {"long_name": "经向风（v 分量）", "standard_name": "northward_wind",
                "units": "m s-1", "missing_value": np.nan}
d.attrs = {
    "title": "NCEP/DOE Reanalysis 2 monthly wind (demo subset, 850hPa)",
    "source": "NCEP/DOE AMIP-II Reanalysis (Reanalysis-2) Model",
    "institution": "National Centers for Environmental Prediction",
    "References": "https://www.psl.noaa.gov/data/gridded/data.ncep.reanalysis2.html",
    "Conventions": "CF-1.0",
}
d.to_netcdf(out, encoding={"u": {"dtype": "float32", "zlib": True, "complevel": 4},
                           "v": {"dtype": "float32", "zlib": True, "complevel": 4}})
print(f"已生成：{out}（{out.stat().st_size / 1e6:.1f} MB）")
