"""NCViewer M1 无头端到端验证。"""
import os
os.environ["MPLBACKEND"] = "Agg"
import matplotlib; matplotlib.use("Agg")
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import matplotlib.pyplot as plt
from core.dataset import open_dataset, describe_variables, get_time_info, slice_var
from plots.spec import PlotSpec
from plots.render import render_map, render_line

data_dir = root / "data"
ds = open_dataset(data_dir / "demo_siconc.nc")
assert any(item["name"] == "siconc" for item in describe_variables(ds))
info = get_time_info(ds, "siconc")
assert "360" in info["calendar"]
da = slice_var(ds, "siconc", {"time": 0})
assert da.ndim == 2
fig = render_map(da, PlotSpec(var_name="siconc", title="海冰密集度"), plt.figure())
fig.savefig(data_dir / "test_map.png"); plt.close(fig)
assert (data_dir / "test_map.png").exists() and (data_dir / "test_map.png").stat().st_size > 0
line = slice_var(ds, "siconc", {"lat": 0, "lon": 0})
fig = render_line(line, PlotSpec(plot_type="line", var_name="siconc", title="时间序列"), plt.figure())
fig.savefig(data_dir / "test_line.png"); plt.close(fig)
assert (data_dir / "test_line.png").exists() and (data_dir / "test_line.png").stat().st_size > 0
print("M1 pipeline tests passed")
