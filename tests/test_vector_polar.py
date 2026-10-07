# -*- coding: utf-8 -*-
"""S7：u/v 矢量识别、自动极地投影、投影中文描述、配色扩充 测试。"""
from __future__ import annotations
import os, sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import xarray as xr

from ncviewer.plots.render import _vector_pair
from ncviewer.ui.plot_controls import _proj_eng, _proj_label, _COLORMAPS

# ---- 1. 矢量对检测 ----
assert _vector_pair(["u", "v"]) == ("u", "v")
assert _vector_pair(["v", "u"]) == ("u", "v")
assert _vector_pair(["U", "V"]) == ("U", "V")
assert _vector_pair(["x_wind", "y_wind"]) == ("x_wind", "y_wind")
assert _vector_pair(["u", "temp"]) is None
assert _vector_pair(["u"]) is None
assert _vector_pair(["u", "v", "temp"]) is None
print("PASS 矢量对检测")

# ---- 2. 投影中文描述 ----
assert _proj_label("NorthPolarStereo") == "北半球极射（NorthPolarStereo）"
assert _proj_label("Robinson") == "罗宾逊（Robinson）"
assert _proj_eng("北半球极射（NorthPolarStereo）") == "NorthPolarStereo"
assert _proj_eng("罗宾逊（Robinson）") == "Robinson"
assert _proj_eng(_proj_label("Mollweide")) == "Mollweide"
print("PASS 投影中文描述双向映射")

# ---- 3. 配色扩充 ----
assert len(_COLORMAPS) >= 30, f"配色应扩充到 30+, 实际 {len(_COLORMAPS)}"
from matplotlib import colormaps
for c in _COLORMAPS:
    assert c in colormaps, f"无效 colormap: {c}"
print(f"PASS 配色扩充 ({len(_COLORMAPS)} 个, 全部有效)")

# ---- 4. 自动极地投影（模块级函数） ----
from ncviewer.ui.plot_window import _auto_polar_projection

# 北极 EASE-Grid 风格：2D 辅助 lat 29.9-90
ny, nx = 20, 30
y = np.arange(ny); x = np.arange(nx)
yy, xx = np.meshgrid(y, x, indexing="ij")
lon2d = 100 + 2.0 * xx + 0.03 * yy
lat2d = 29.9 + 2.0 * yy + 0.02 * xx  # 29.9~90
ds_arctic = xr.Dataset(
    {"u": (("y", "x"), np.random.rand(ny, nx)),
     "lon": (("y", "x"), lon2d, {"units": "degrees_east"}),
     "lat": (("y", "x"), lat2d, {"units": "degrees_north"})},
    coords={"y": y, "x": x})
ds_arctic = ds_arctic.set_coords(["lon", "lat"])
assert _auto_polar_projection(ds_arctic["u"]) == "NorthPolarStereo", "北极应自动北半球极射"
print("PASS 北极数据自动 NorthPolarStereo")

# 南极
lat2d_s = -29.9 - 2.0 * yy - 0.02 * xx  # -29.9~-90
ds_antarctic = xr.Dataset(
    {"v": (("y", "x"), np.random.rand(ny, nx)),
     "lon": (("y", "x"), lon2d, {"units": "degrees_east"}),
     "lat": (("y", "x"), lat2d_s, {"units": "degrees_north"})},
    coords={"y": y, "x": x})
ds_antarctic = ds_antarctic.set_coords(["lon", "lat"])
assert _auto_polar_projection(ds_antarctic["v"]) == "SouthPolarStereo", "南极应自动南半球极射"
print("PASS 南极数据自动 SouthPolarStereo")

# 全球数据不自动切
ds_global = xr.Dataset(
    {"g": (("lat", "lon"), np.random.rand(10, 12))},
    coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(0, 360, 12)})
assert _auto_polar_projection(ds_global["g"]) is None, "全球数据不应自动切极射"
print("PASS 全球数据不自动切极射")

print("\nALL PASS")
