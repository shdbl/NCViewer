"""B3 时间-纬度 Hovmöller 渲染验证。"""
from __future__ import annotations

import os
os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path
import sys

import cftime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ncviewer.core.dataset import open_dataset, slice_var
from ncviewer.plots.render import render
from ncviewer.plots.spec import PlotSpec


time = xr.cftime_range("2001-01-01", periods=12, freq="MS", calendar="360_day")
lat = np.linspace(-90, 90, 73)
values = np.sin(np.arange(12)[:, None] / 3) * np.cos(np.deg2rad(lat))[None, :]
da = xr.DataArray(values, dims=("time", "lat"), coords={"time": time, "lat": lat},
                  name="siconc")
fig = plt.figure()
render(da, PlotSpec(var_name="siconc"), fig)
assert fig.axes, "Hovmöller 图应至少包含一个坐标轴"
assert len(fig.axes) >= 2, "Hovmöller 图默认应包含色标"
plt.close(fig)

data_dir = Path(__file__).resolve().parents[1] / "data"
ds = open_dataset(data_dir / "demo_siconc.nc")
map_data = slice_var(ds, "siconc", {"time": 0})
fig = plt.figure()
render(map_data, PlotSpec(var_name="siconc"), fig)
assert fig.axes, "演示数据地图分支不应受 Hovmöller 自动识别影响"
plt.close(fig)

assert isinstance(time[0], cftime.datetime)
print("B3 时间-纬度剖面测试通过")
