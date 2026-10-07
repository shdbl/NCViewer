# -*- coding: utf-8 -*-
"""S7.2：CF grid_mapping 投影坐标网格 测试。"""
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr

from ncviewer.core.dataset import get_grid_mapping
from ncviewer.plots.render import _projected_crs, _projected_xy, _aux_lon_lat
from ncviewer.ui.plot_window import _auto_polar_projection

# ---- 构造投影网格数据（模拟 EASE-Grid North：x/y 投影坐标 + crs） ----
ny, nx = 20, 30
x = np.linspace(-2000000, 2000000, nx)
y = np.linspace(-2000000, 2000000, ny)
data = np.random.rand(ny, nx)
ds = xr.Dataset(
    {"var": (("y", "x"), data)},
    coords={"y": y, "x": x},
    attrs={})
ds["var"].attrs["grid_mapping"] = "crs"
ds["crs"] = xr.DataArray(
    -2147483647,
    attrs={
        "grid_mapping_name": "lambert_azimuthal_equal_area",
        "longitude_of_projection_origin": 0.0,
        "latitude_of_projection_origin": 90.0,
        "semi_major_axis": 6371228.0,
        "inverse_flattening": 0.0,
    })

# ---- 1. grid_mapping 解析 ----
gm = get_grid_mapping(ds, "var")
assert gm is not None, "应识别 grid_mapping"
assert gm["grid_mapping_name"] == "lambert_azimuthal_equal_area"
assert gm["latitude_of_projection_origin"] == 90.0
assert gm["semi_major_axis"] == 6371228.0
print("PASS grid_mapping 解析")

# 无 grid_mapping 的变量返回 None
ds2 = ds.drop_vars("var")
ds2["plain"] = (("y", "x"), data)
assert get_grid_mapping(ds2, "plain") is None
print("PASS 无 grid_mapping 返回 None")

# ---- 2. 投影 CRS ----
crs = _projected_crs(gm)
assert "LambertAzimuthalEqualArea" in type(crs).__name__, type(crs).__name__
# 自定义球体（semi_major_axis）必须生效
assert abs(crs.globe.semimajor_axis - 6371228.0) < 1.0, f"球体半径错误: {crs.globe.semimajor_axis}"
print("PASS 投影 CRS + 自定义球体")

# ---- 3. x/y 网格 ----
xy = _projected_xy(ds["var"], gm)
assert xy is not None
x2d, y2d, x_dim, y_dim = xy
assert x2d.shape == (ny, nx) and y2d.shape == (ny, nx)
print("PASS x/y 投影网格构建")

# ---- 4. 自动极地投影（grid_mapping lat_0=90 → 北极） ----
assert _auto_polar_projection(ds["var"], gm) == "NorthPolarStereo"
# 南极投影
gm_south = dict(gm)
gm_south["latitude_of_projection_origin"] = -90.0
assert _auto_polar_projection(ds["var"], gm_south) == "SouthPolarStereo"
# 无 grid_mapping 时走纬度范围判定
assert _auto_polar_projection(ds["var"], None) is None  # x/y 无 lat 坐标
print("PASS 投影网格自动极地投影")

# ---- 5. 常规经纬度数据不受 grid_mapping 干扰 ----
ds3 = xr.Dataset(
    {"g": (("lat", "lon"), np.random.rand(10, 12))},
    coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(0, 360, 12)})
assert get_grid_mapping(ds3, "g") is None
assert _auto_polar_projection(ds3["g"]) is None
print("PASS 常规经纬度不受影响")

print("\nALL PASS")
