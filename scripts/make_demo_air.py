"""从真实 NCEP/DOE Reanalysis 2 数据生成 demo_air.nc。

- 数据源：D:\\data\\air.mon.mean.nc（NCEP/DOE AMIP-II Reanalysis，全球月平均气温）
  （https://www.psl.noaa.gov/data/gridded/data.ncep.reanalysis2.html，公共领域）
- 截取：最近 12 个月（2024-10 ~ 2025-09），保留全部 17 个气压层、73×144 全球网格
- 保留 level 维：NCViewer 会为它生成"额外维度切片器"（Panoply 式逐维选择），
  同时展示多层气压场能力
"""
from pathlib import Path
import xarray as xr

root = Path(__file__).resolve().parents[1]
src = r"D:\data\air.mon.mean.nc"
out = root / "data" / "demo_air.nc"

ds = xr.open_dataset(src)
air = ds["air"]  # (time, level, lat, lon)
print(f"源数据：{air.shape}，time {str(air.time.values[0])[:10]} ~ {str(air.time.values[-1])[:10]}")

# 最近 12 个月
demo = air.isel(time=slice(-12, None))
print(f"截取 12 个月：{str(demo.time.values[0])[:10]} ~ {str(demo.time.values[-1])[:10]}，"
      f"shape {demo.shape}，{demo.nbytes / 1e6:.1f} MB")

d = demo.to_dataset(name="air")
# 保留源文件的全局属性（来源信息，README 可引用）
d.attrs = {
    "title": "NCEP/DOE Reanalysis 2 monthly mean air temperature (demo subset)",
    "source": "NCEP/DOE AMIP-II Reanalysis (Reanalysis-2) Model",
    "institution": "National Centers for Environmental Prediction",
    "References": "https://www.psl.noaa.gov/data/gridded/data.ncep.reanalysis2.html",
    "Conventions": "CF-1.0",
}
d.to_netcdf(out, encoding={"air": {"dtype": "float32", "zlib": True, "complevel": 4}})
print(f"已生成：{out}（{out.stat().st_size / 1e6:.1f} MB）")
