# -*- coding: utf-8 -*-
"""curvilinear grid（2D 辅助经纬度）支持测试。"""
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr

from ncviewer.core.dataset import find_aux_lonlat, get_aux_lonlat_arrays
from ncviewer.plots.render import _aux_lon_lat, render_map
from ncviewer.plots.spec import spec_from_defaults
from ncviewer.ui.datatree import _var_type_text

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- 构造 curvilinear grid 数据（模拟旋转极网格） ----
ny, nx = 20, 30
y = np.arange(ny); x = np.arange(nx)
# 弯曲经纬度：(y,x) 网格，lon/lat 随位置非线性变化 → 网格弯曲
yy, xx = np.meshgrid(y, x, indexing="ij")
lon2d = 100 + 2.0 * xx + 0.03 * yy   # (y,x)
lat2d = 30 + 1.0 * yy + 0.02 * xx    # (y,x)
data = 50 + 30 * np.cos(np.radians(lat2d)) * np.sin(np.radians(lon2d - 100))
ds = xr.Dataset(
    {
        "var": (("y", "x"), data),
        "lon": (("y", "x"), lon2d, {"units": "degrees_east"}),
        "lat": (("y", "x"), lat2d, {"units": "degrees_north"}),
    },
    coords={"y": y, "x": x},
)
ds["var"].attrs["coordinates"] = "lon lat"
# CF 约定：2D 辅助坐标作为数据集的坐标（curvilinear grid 的标准表示）
ds = ds.set_coords(["lon", "lat"])

# ---- 1. 识别 ----
f = find_aux_lonlat(ds, "var")
assert f == ("lon", "lat"), f"识别失败: {f}"
print("PASS 识别: find_aux_lonlat ->", f)

# ---- 2. render 层检测 ----
aux = _aux_lon_lat(ds["var"])
assert aux is not None, "_aux_lon_lat 未识别"
print("PASS render _aux_lon_lat:", aux[0].name, aux[1].name)

# ---- 3. 渲染 ----
spec = spec_from_defaults("var")
spec.plot_type = "map"
fig = plt.figure(figsize=(7, 5))
render_map(ds["var"], spec, fig)
fig.savefig(r"D:\Agent\deepseek\ncviewer\data\_aux_curvi_test.png", dpi=90)
plt.close(fig)
print("PASS 渲染 curvilinear 地图（截图已保存）")

# ---- 4. 类型文字 ----
desc = {"name": "var", "dims": ("y", "x"), "shape": (ny, nx)}
t = _var_type_text(desc, ds)
assert t == "曲线网格经纬度场", f"类型文字: {t}"
print("PASS 类型文字:", t)

# 无 ds 时回退二维平面
t2 = _var_type_text(desc)
assert t2 == "二维平面", f"无 ds 回退: {t2}"
print("PASS 无 ds 回退:", t2)

# ---- 5. 常规经纬度数据不受影响 ----
ds2 = xr.Dataset({"v": (("lat", "lon"), np.random.rand(10, 12))},
                 coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(0, 360, 12)})
assert find_aux_lonlat(ds2, "v") is None
assert _aux_lon_lat(ds2["v"]) is None
print("PASS 常规经纬度数据不误判为辅助坐标")

# ---- 6. 3D（time+y/x+辅助坐标）识别：未切片也要能判 map ----
ds3 = xr.Dataset(
    {
        "v3": (("time", "y", "x"), np.random.rand(3, ny, nx)),
        "lon": (("y", "x"), lon2d, {"units": "degrees_east"}),
        "lat": (("y", "x"), lat2d, {"units": "degrees_north"}),
    },
    coords={"time": [0, 1, 2], "y": y, "x": x},
)
ds3["v3"].attrs["coordinates"] = "lon lat"
ds3 = ds3.set_coords(["lon", "lat"])
assert _aux_lon_lat(ds3["v3"]) is not None, "3D 未切片辅助坐标应能识别（否则投影组灰掉）"
assert _aux_lon_lat(ds3["v3"].isel(time=0)) is not None
print("PASS 3D 未切片/切片后辅助坐标均识别")

# ---- 7. 3D 常规经纬度（time,lat,lon）不误判 ----
ds4 = xr.Dataset(
    {"v4": (("time", "lat", "lon"), np.random.rand(3, 10, 12))},
    coords={"time": [0, 1, 2],
            "lat": np.linspace(-90, 90, 10), "lon": np.linspace(0, 360, 12)})
assert _aux_lon_lat(ds4["v4"]) is None
print("PASS 3D 常规经纬度不误判为辅助坐标")

# ---- 8. 辅助坐标是 data_vars 未 set_coords（只靠 coordinates 属性） ----
dsA = xr.Dataset(
    {"varA": (("y", "x"), np.random.rand(ny, nx)),
     "lon": (("y", "x"), lon2d, {"units": "degrees_east"}),
     "lat": (("y", "x"), lat2d, {"units": "degrees_north"})},
    coords={"y": y, "x": x})
dsA["varA"].attrs["coordinates"] = "lon lat"
# 不 set_coords：lon/lat 是 data_vars，裸 da.coords 里没有 → _aux_lon_lat 识别不到
# （真实渲染路径由 plot_window._attach_aux_coords 从 Dataset 补齐）
assert find_aux_lonlat(dsA, "varA") == ("lon", "lat")
assert _aux_lon_lat(dsA["varA"]) is None  # 裸 da 看不到 data_vars（预期）
# 模拟 attach（plot_window 的补齐逻辑）
daA = dsA["varA"].assign_coords(lon=dsA["lon"], lat=dsA["lat"])
assert _aux_lon_lat(daA) is not None, "attach 后辅助坐标应识别"
print("PASS data_vars 辅助坐标经 attach 后识别")

# ---- 9. 非标准名 nav_lon/nav_lat（standard_name 匹配） ----
dsC = xr.Dataset(
    {"varC": (("y", "x"), np.random.rand(ny, nx)),
     "nav_lon": (("y", "x"), lon2d, {"standard_name": "longitude", "units": "degrees_east"}),
     "nav_lat": (("y", "x"), lat2d, {"standard_name": "latitude", "units": "degrees_north"})},
    coords={"y": y, "x": x})
dsC["varC"].attrs["coordinates"] = "nav_lon nav_lat"
assert find_aux_lonlat(dsC, "varC") == ("nav_lon", "nav_lat")
daC = dsC["varC"].assign_coords(nav_lon=dsC["nav_lon"], nav_lat=dsC["nav_lat"])
assert _aux_lon_lat(daC) is not None, "standard_name 辅助坐标识别"
print("PASS nav_lon/nav_lat（standard_name）识别")

print("\nALL PASS")
