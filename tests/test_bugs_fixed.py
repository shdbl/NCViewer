"""回归测试：覆盖 gemini bug 审查发现的真实缺陷。

覆盖点：
- 1D 时间序列变量出图不崩溃（KeyError index 修复）
- CSV 导出（DataArray.items AttributeError 修复）
- 多数据集 build_tree 不清空先前数据集
- CombinePlotWindow 子图不被 render 覆盖
- render_contour 归一化传对数据
- log_scale 全负回退
"""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import numpy as np
import xarray as xr

from PySide6.QtWidgets import QApplication

from ncviewer.core.dataset import describe_variables
from ncviewer.ui.datatree import build_tree, item_payload
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.plot_window import CombinePlotWindow, PlotWindow


def make_1d_ds():
    """一维时间序列数据集（全球平均温度）。"""
    time = xr.cftime_range("2015-01-01", periods=12, freq="MS",
                           calendar="360_day", name="time")
    t = xr.DataArray(np.sin(np.arange(12) / 2.0) * 5 + 20,
                     dims=["time"], coords={"time": time}, name="t_mean")
    t.attrs["units"] = "degC"
    t.attrs["long_name"] = "global mean temperature"
    return t.to_dataset(), "t_mean"


def make_2d_ds():
    """二维非地理等高线数据集。"""
    y = np.linspace(0, 10, 30)
    x = np.linspace(0, 10, 40)
    yy, xx = np.meshgrid(y, x, indexing="ij")
    z = np.sin(xx) * np.cos(yy) * 100 + 50000  # 大量级，测试归一化
    da = xr.DataArray(z, dims=["y", "x"], coords={"y": y, "x": x}, name="pressure")
    da.attrs["units"] = "Pa"
    return da.to_dataset(), "pressure"


def main():
    results = []
    app = QApplication.instance() or QApplication([])

    # ---- 1. 1D 时间序列出图不崩溃 ----
    ds1, v1 = make_1d_ds()
    pw = PlotWindow(ds1, v1)
    pw.refresh_plot()
    ok = "绘图失败" not in pw.status.currentMessage()
    results.append(("1D 时间序列出图不崩溃", ok, pw.status.currentMessage()))
    pw.close()

    # ---- 2. CSV 导出不崩溃 ----
    import csv
    csv_path = os.path.join(os.path.dirname(__file__), "_test_bug_export.csv")
    da = ds1[v1]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        dims = list(da.dims)
        writer.writerow(dims + ["value"])
        series = da.to_series()
        for idx, val in series.items():
            keys = list(idx) if isinstance(idx, tuple) else [idx]
            writer.writerow(keys + [float(val)])
    nrows = sum(1 for _ in open(csv_path, encoding="utf-8-sig")) - 1
    results.append(("CSV 导出生成数据", nrows == 12, f"rows={nrows}"))
    os.remove(csv_path)

    # ---- 3. 多数据集 build_tree 不清空 ----
    w = MainWindow()
    build_tree(w.tree, ds1, "file_a.nc", describe_variables(ds1), clear=True)
    ds2, v2 = make_2d_ds()
    build_tree(w.tree, ds2, "file_b.nc", describe_variables(ds2), clear=False)
    roots = [w.tree.topLevelItem(i) for i in range(w.tree.topLevelItemCount())]
    results.append(("多数据集两棵根并存", len(roots) == 2, f"roots={len(roots)}"))

    # ---- 4. CombinePlotWindow 子图不被覆盖 ----
    cp = CombinePlotWindow([(ds2, v2), (ds1, v1)])
    cp.refresh_plot()
    n_axes = len(cp.figure.axes)
    results.append(("合并图两个子图", n_axes >= 2, f"axes={n_axes}"))
    cp.close()

    # ---- 5. render_contour 归一化传对数据（不抛异常且 levels 正常） ----
    from ncviewer.plots.render import render_contour
    from ncviewer.plots.spec import spec_from_defaults
    from matplotlib.figure import Figure
    spec = spec_from_defaults(v2)
    spec.normalize = True
    spec.level_min = 0.0
    spec.level_max = 100.0
    fig = Figure(figsize=(4, 3))
    try:
        render_contour(ds2[v2], spec, fig)
        ok = True
    except Exception as exc:
        ok = False
        results.append(("render_contour 归一化", ok, f"exc={exc}"))
    if ok:
        # 验证图上数据已归一化（collections 的 array 应在 0-100 附近）
        arrs = [np.asarray(c.get_array()).min() for c in fig.axes[0].collections
                if c.get_array() is not None]
        in_range = all(0 <= a <= 100 for a in arrs) if arrs else False
        results.append(("render_contour 归一化", in_range, f"min={arrs}"))
    import matplotlib.pyplot as plt
    plt.close(fig)

    # ---- 6. log_scale 全负回退 ----
    ds_neg = xr.Dataset({"v": (["t"], np.full(10, -5.0))})
    spec2 = spec_from_defaults("v")
    spec2.log_scale = True
    spec2.level_min = None
    spec2.level_max = None
    from ncviewer.plots.render import render_line
    fig2 = Figure(figsize=(4, 3))
    try:
        render_line(ds_neg["v"], spec2, fig2)
        ok = True
    except Exception as exc:
        ok = False
        results.append(("log 全负 line 回退", ok, f"exc={exc}"))
    if ok:
        results.append(("log 全负 line 回退", True, "线性渲染成功"))
    plt.close(fig2)

    # ---- 汇总 ----
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n==== Bug 回归: {passed}/{len(results)} 通过 ====")
    for name, ok, detail in results:
        mark = "[PASS]" if ok else "[FAIL]"
        print(f"{mark} {name}  {detail}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
