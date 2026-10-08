"""NCViewer M1 无头端到端验证（真实 demo 数据：NCEP air + NSIDC CDR v6 sic）。"""
import os
os.environ["MPLBACKEND"] = "Agg"
import matplotlib; matplotlib.use("Agg")
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))  # D:\Agent\deepseek，让 ncviewer 包可解析
sys.path.insert(0, str(root))
import matplotlib.pyplot as plt
from ncviewer.core.dataset import open_dataset, describe_variables, get_time_info, slice_var
from ncviewer.plots.spec import PlotSpec
from ncviewer.plots.render import render_map, render_line

data_dir = root / "data"

# ---- demo_siconc.nc（NSIDC CDR v6 真实海冰，y/x 维 + 2D 辅助经纬度 + grid_mapping）----
ds = open_dataset(data_dir / "demo_siconc.nc")
assert any(item["name"] == "sic" for item in describe_variables(ds))
info = get_time_info(ds, "sic")
assert "standard" in info["calendar"] or "proleptic" in info["calendar"]
# 时间切片：真实数据是 (time, y, x)，切 time 后是 2D
da = slice_var(ds, "sic", {"time": 0})
assert da.ndim == 2
fig = render_map(da, PlotSpec(var_name="sic", title="海冰密集度"), plt.figure())
fig.savefig(data_dir / "test_map.png"); plt.close(fig)
assert (data_dir / "test_map.png").exists() and (data_dir / "test_map.png").stat().st_size > 0
# 时间序列：用 y/x 维切片（真实数据没有 lat/lon 一维坐标）
line = slice_var(ds, "sic", {"y": 0, "x": 0})
fig = render_line(line, PlotSpec(plot_type="line", var_name="sic", title="时间序列"), plt.figure())
fig.savefig(data_dir / "test_line.png"); plt.close(fig)
assert (data_dir / "test_line.png").exists() and (data_dir / "test_line.png").stat().st_size > 0

# ---- demo_air.nc（NCEP Reanalysis 2 真实气温，time/level/lat/lon）----
ds_air = open_dataset(data_dir / "demo_air.nc")
assert any(item["name"] == "air" for item in describe_variables(ds_air))
info_air = get_time_info(ds_air, "air")
assert len(ds_air["air"].time) == 12
air_slice = slice_var(ds_air, "air", {"time": 0, "level": 0})
assert air_slice.ndim == 2
fig = render_map(air_slice, PlotSpec(var_name="air", title="气温"), plt.figure())
fig.savefig(data_dir / "test_air_map.png"); plt.close(fig)
assert (data_dir / "test_air_map.png").exists() and (data_dir / "test_air_map.png").stat().st_size > 0

print("M1 pipeline tests passed")
