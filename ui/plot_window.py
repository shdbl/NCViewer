"""绘图窗口（Panoply 范式）：三视图 可视化|查看数据|查看元数据。

- 标题：`{变量短名} in {数据集名}`（Panoply 风格）。
- 顶部 Panoply 式时间选择器：`时次: [1 of 12 = 2015-01-01]`（spinner+combo 联动）。
- 可视化视图：matplotlib FigureCanvas + 工具栏 + 滑块。
- 查看数据视图：数据表格（带行列索引）。
- 查看元数据视图：CDL 等宽全文。
- 右侧 QDockWidget「绘图设置」= PlotControlsPanel。
"""
from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox, QDockWidget, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from ncviewer.core.dataset import get_time_info
from ncviewer.plots.render import _is_hovmoller, render
from ncviewer.plots.spec import spec_from_defaults
from ncviewer.ui.icons import app_icon, panoply_icon, play_icon, step_left_icon, step_right_icon
from ncviewer.ui.metadata_panel import cdl_html
from ncviewer.ui.plot_controls import PlotControlsPanel, _NoWheelCombo


def _time_strings(ds, var_name: str) -> list[str]:
    """取变量时间坐标的全部格式化字符串（兼容 cftime）。"""
    da = ds[var_name]
    time_name = next((d for d in da.dims if d.lower() in {"time", "times"}),
                     next((d for d in da.dims if "time" in d.lower()), None))
    if time_name is None:
        return []
    coord = ds[time_name]
    out = []
    import pandas as pd
    for v in coord.values:
        if hasattr(v, "strftime"):
            out.append(v.strftime("%Y-%m-%d"))
        else:
            # numpy.datetime64 无 strftime：转 pandas Timestamp 再格式化
            out.append(pd.Timestamp(v).strftime("%Y-%m-%d"))
    return out


def _fmt_coord(v) -> str:
    """坐标值格式化：浮点取紧凑形式，其它转字符串。"""
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _auto_polar_projection(da, grid_mapping=None) -> str | None:
    """极区数据自动选投影：只覆盖北极 → NorthPolarStereo，只覆盖南极 → SouthPolarStereo。

    判定优先级：
    1. CF grid_mapping（投影网格）：由投影原点纬度 lat_0 判断（90→北极，-90→南极）；
    2. 取数据纬度坐标（1D lat 维或 2D 辅助 lat），看有效纬度范围。
    返回投影英文名，不适合自动切换返回 None。
    """
    import numpy as np
    from ncviewer.plots.render import _aux_lon_lat
    # 1) 投影网格：用投影原点纬度
    if grid_mapping:
        try:
            lat0 = float(grid_mapping.get("latitude_of_projection_origin", 0.0))
        except (TypeError, ValueError):
            lat0 = 0.0
        name = grid_mapping.get("grid_mapping_name", "")
        if lat0 >= 60:
            return "NorthPolarStereo"
        if lat0 <= -60:
            return "SouthPolarStereo"
    lat = None
    # 优先 2D 辅助纬度
    aux = _aux_lon_lat(da)
    if aux is not None:
        lat = np.asarray(aux[1].values, dtype=float)
    else:
        lat_dim = next((d for d in da.dims if d.lower() in {"lat", "latitude"}), None)
        if lat_dim is not None and lat_dim in da.coords:
            lat = np.asarray(da.coords[lat_dim].values, dtype=float)
    if lat is None or lat.size == 0:
        return None
    finite = lat[np.isfinite(lat)]
    if finite.size == 0:
        return None
    lat_min, lat_max = float(np.min(finite)), float(np.max(finite))
    # 北极：全部纬度 ≥ 25°N 且最高 ≥ 60°N（排除全球/南半球数据）
    # EASE-Grid North 最低纬约 29.9°N，阈值留余量
    if lat_min >= 25 and lat_max >= 60:
        return "NorthPolarStereo"
    # 南极：全部纬度 ≤ -25°S 且最低 ≤ -60°S
    if lat_max <= -25 and lat_min <= -60:
        return "SouthPolarStereo"
    return None


class PlotWindow(QMainWindow):
    """单个变量的绘图窗口。"""

    def __init__(self, ds, var_name: str, parent=None):
        super().__init__(parent)
        self.dataset = ds
        self.var_name = var_name
        self.spec = spec_from_defaults(var_name)
        self.time_strings = _time_strings(ds, var_name)
        self._time_index = 0
        self._reentrant = False
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(250)
        self._anim_timer.timeout.connect(self._anim_step)
        # 额外层次维度（level/height/pressure 等，非 time/lat/lon）——Panoply 式每维一行切片器
        self._extra_dims = self._detect_extra_dims(ds, var_name)  # [(dim, values), ...]
        self._extra_indices = [0] * len(self._extra_dims)

        # 标题：变量 in 数据集（Panoply 风格，截断保护）
        vname = var_name.replace("_", " ")[:28]
        dname = _ds_name(ds)[:42]
        self.setWindowTitle(f"{vname} in {dname}")
        self.setWindowIcon(app_icon(48))
        self.resize(980, 700)

        self._build_tabs()
        self._build_dock()
        self._build_menu()
        self.refresh_plot()
        self.fit_scale()
        self._sync_time_widgets()

    # ---------- UI ----------
    def _build_tabs(self):
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        self.time_bar = self._make_time_bar()
        outer.addWidget(self.time_bar)
        self.slicer_bar = self._build_slicer_bar()
        if self.slicer_bar is not None:
            outer.addWidget(self.slicer_bar)

        self.tabs = QTabWidget()
        # 视图1：可视化
        self.figure = Figure(figsize=(7, 5.2), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.plot_host = QWidget()
        ph_lay = QVBoxLayout(self.plot_host)
        ph_lay.setContentsMargins(0, 0, 0, 0)
        ph_lay.addWidget(self.canvas)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        ph_lay.addWidget(self.toolbar)
        self.tabs.addTab(self.plot_host, "可视化")

        # 视图2：查看数据
        self.data_table = QTableWidget()
        self.data_host = QWidget()
        dh_lay = QVBoxLayout(self.data_host)
        dh_lay.setContentsMargins(4, 4, 4, 4)
        dh_lay.setSpacing(4)
        # 维度标注行（Panoply View Data 的 X/Y Axis 标签）
        self.table_info = QLabel("")
        self.table_info.setObjectName("tableInfo")
        dh_lay.addWidget(self.table_info)
        dh_lay.addWidget(self.data_table)
        # 数字格式下拉（Panoply Data Format）
        fmt_row = QHBoxLayout()
        fmt_lbl = QLabel("数字格式")
        fmt_lbl.setObjectName("dimLabel")
        self.data_format_combo = _NoWheelCombo()
        self.data_format_combo.addItems(["%.1f", "%.2f", "%.3f", "%.4g", "%.7G"])
        self.data_format_combo.setCurrentText("%.4g")
        self.data_format_combo.setToolTip("表格中数值的显示格式（可调小数位数）")
        self.data_format_combo.currentTextChanged.connect(lambda _: self._refill_data_table())
        fmt_row.addWidget(fmt_lbl)
        fmt_row.addWidget(self.data_format_combo)
        fmt_row.addStretch(1)
        dh_lay.addLayout(fmt_row)
        self.tabs.addTab(self.data_host, "查看数据")

        # 视图3：查看元数据（结构化 HTML：变量名标题 + 键值行）
        self.meta_view = QTextEdit()
        self.meta_view.setObjectName("rawInfo")
        self.meta_view.setReadOnly(True)
        self.meta_view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.tabs.addTab(self.meta_view, "查看元数据")

        outer.addWidget(self.tabs)
        self.setCentralWidget(central)

        self.status = self.statusBar()
        self.status.showMessage("就绪")

    # ---------- 额外维度检测（Panoply：所有自由维各一行切片器） ----------
    @staticmethod
    def _detect_extra_dims(ds, var_name):
        """检测变量除 time/lat/lon（绘图轴）外的全部额外维度。

        返回 [(dim_name, values列表), ...]；无额外维返回 []。
        对齐 Panoply getFreeDimensions：每个非绘图维一个切片器。
        """
        da = ds[var_name]
        reserved = {"time", "times"}
        latlon = {"lat", "latitude", "y", "lon", "longitude", "x"}
        result = []
        for d in da.dims:
            low = d.lower()
            if low in reserved or low in latlon or "time" in low:
                continue
            values = ds[d].values if d in ds.coords else list(range(da.sizes[d]))
            result.append((d, list(values)))
        return result

    def _make_time_bar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        self.time_label = QLabel("时次")
        self.time_label.setObjectName("timeValue")
        lay.addWidget(self.time_label)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, max(1, len(self.time_strings)))
        self.time_spin.setToolTip("时次序号（可手动输入）")
        self.time_spin.setFixedWidth(70)
        lay.addWidget(self.time_spin)

        self.time_combo = _NoWheelCombo()
        self.time_combo.addItems(self.time_strings or ["—"])
        self.time_combo.setMinimumWidth(120)
        lay.addWidget(self.time_combo)

        self.btn_prev = QToolButton()
        self.btn_prev.setIcon(step_left_icon(22))
        self.btn_prev.setToolTip("上一时次")
        self.btn_prev.setFixedSize(34, 32)
        lay.addWidget(self.btn_prev)

        self.btn_next = QToolButton()
        self.btn_next.setIcon(step_right_icon(22))
        self.btn_next.setToolTip("下一时次")
        self.btn_next.setFixedSize(34, 32)
        lay.addWidget(self.btn_next)

        self.play = QToolButton()
        self.play.setIcon(play_icon(22))
        self.play.setToolTip("播放动画")
        self.play.setCheckable(True)
        self.play.setFixedSize(34, 32)
        lay.addWidget(self.play)

        self.speed_btn = QToolButton()
        self.speed_btn.setText("速度")
        self.speed_btn.setObjectName("speedButton")
        self.speed_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.speed_btn.setToolTip("动画播放速度")
        self.speed_menu = QMenu(self)
        self._anim_speeds = [("慢 0.5×", 500), ("正常 1×", 250),
                             ("快 2×", 125), ("极快 4×", 62)]
        for label, ms in self._anim_speeds:
            act = self.speed_menu.addAction(label)
            act.triggered.connect(lambda _=False, m=ms, t=label: self._set_anim_speed(m, t))
        self.speed_btn.setMenu(self.speed_menu)
        lay.addWidget(self.speed_btn)

        lay.addSpacing(8)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, max(0, len(self.time_strings) - 1))
        self.slider.setFixedHeight(22)
        lay.addWidget(self.slider, 1)

        # 信号连接（Panoply 式四控件联动）
        self.time_spin.valueChanged.connect(self._on_spin_time)
        self.time_combo.currentIndexChanged.connect(self._on_combo_time)
        self.slider.valueChanged.connect(self._on_slider)
        self.btn_prev.clicked.connect(lambda: self._step_time(-1))
        self.btn_next.clicked.connect(lambda: self._step_time(1))
        self.play.toggled.connect(self._on_play_toggled)

        return bar

    def _build_slicer_bar(self) -> QWidget:
        """Panoply 式额外维度切片器：每个自由维一行（维名: spin of N = combo 值）。

        无额外维时返回 None（隐藏）。
        """
        if not self._extra_dims:
            return None
        bar = QWidget()
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(4, 0, 4, 2)
        lay.setSpacing(2)
        self._slicer_spins = []
        self._slicer_combos = []
        self._slicer_labels = []
        for i, (dim, values) in enumerate(self._extra_dims):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(6)
            label = QLabel(f"{dim}:")
            label.setObjectName("dimLabel")
            rl.addWidget(label)
            spin = QSpinBox()
            spin.setRange(1, max(1, len(values)))
            spin.setToolTip(f"{dim} 序号（可手动输入）")
            spin.setFixedWidth(56)
            rl.addWidget(spin)
            of_lbl = QLabel(f"of {len(values)} =")
            of_lbl.setObjectName("dimLabel")
            rl.addWidget(of_lbl)
            combo = _NoWheelCombo()
            combo.setToolTip(f"{dim} 值")
            combo.setMinimumWidth(80)
            combo.addItems([_fmt_coord(v) for v in values])
            rl.addWidget(combo)
            rl.addStretch(1)
            lay.addWidget(row)
            self._slicer_spins.append(spin)
            self._slicer_combos.append(combo)
            self._slicer_labels.append(label)
            spin.valueChanged.connect(lambda v, ii=i: self._on_slicer_spin(ii, v))
            combo.currentIndexChanged.connect(lambda idx, ii=i: self._on_slicer_combo(ii, idx))
        return bar

    def _build_dock(self):
        self.controls_panel = PlotControlsPanel(self)
        dock = QDockWidget("绘图设置", self)
        dock.setObjectName("plotControlsDock")
        # 固定停靠，不可悬浮/移动/关闭
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setWidget(self.controls_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.controls_dock = dock
        # 根据当前变量类型确定绘图类型
        self._apply_plot_type()

    def _build_menu(self):
        mbar = self.menuBar()
        file_menu = mbar.addMenu("文件")
        act_export = QAction("导出图像", self)
        act_export.setShortcut("Ctrl+S")
        act_export.triggered.connect(self._export_png)
        file_menu.addAction(act_export)
        act_csv = QAction("导出数据 CSV", self)
        act_csv.triggered.connect(self._export_csv)
        file_menu.addAction(act_csv)
        act_anim = QAction("导出动画 GIF", self)
        act_anim.triggered.connect(self._export_animation)
        file_menu.addAction(act_anim)
        act_close = QAction("关闭窗口", self)
        act_close.triggered.connect(self.close)
        file_menu.addAction(act_close)

        view_menu = mbar.addMenu("视图")
        act_toggle = QAction("绘图设置", self)
        act_toggle.setCheckable(True)
        act_toggle.setChecked(True)
        act_toggle.triggered.connect(lambda on: self.controls_dock.setVisible(on))
        view_menu.addAction(act_toggle)

    # ---------- 状态 ----------
    def _apply_plot_type(self):
        """根据数据形状决定绘图类型（map / line / contour / hovmoller）。

        带 CF grid_mapping（投影坐标网格）、2D 辅助经纬度坐标或常规经纬度维 → map；
        否则 1D → line，2D+ → contour。极区数据自动切换极地投影。
        """
        from ncviewer.core.dataset import get_grid_mapping
        from ncviewer.plots.render import _aux_lon_lat
        da = self._attach_aux_coords(self.dataset[self.var_name])
        # CF 投影坐标网格：读 grid_mapping 参数 → map（数据用自身投影坐标画）
        gm = get_grid_mapping(self.dataset, self.var_name)
        self.spec._grid_mapping = gm
        if _is_hovmoller(da):
            self.spec.plot_type = "hovmoller"
        elif da.ndim == 1:
            self.spec.plot_type = "line"
        else:
            has_gm = gm is not None
            has_aux = _aux_lon_lat(da) is not None
            has_lat = any(d.lower() in {"lat", "latitude"} for d in da.dims)
            has_lon = any(d.lower() in {"lon", "longitude"} for d in da.dims)
            # 注意：y/x 单独不算经纬度（可能是一般 XY 轴名）；只有明确 lat/lon
            # 或存在 2D 辅助经纬度坐标 / grid_mapping 才走地图
            self.spec.plot_type = "map" if (has_gm or has_aux or (has_lat and has_lon)) else "contour"
        if self.spec.plot_type == "map":
            proj = _auto_polar_projection(da, gm)
            if proj:
                self.spec.projection = proj
        self.controls_panel.set_plot_type(self.spec.plot_type)
        self.controls_panel._sync_from_spec()

    def on_variable_combo_changed(self, idx):
        """绘图设置面板切换变量：重建默认配置（保留布局）。

        用下拉框当前文本而不是位置下标，避免与变量列表提取规则不一致造成错位。
        """
        combo = self.controls_panel.variable_combo
        text = combo.currentText() if combo.count() else None
        if not text or text == self.var_name:
            return
        self.var_name = text
        self.spec = spec_from_defaults(self.var_name)
        # 重置额外维检测与切片器
        self._extra_dims = self._detect_extra_dims(self.dataset, self.var_name)
        self._extra_indices = [0] * len(self._extra_dims)
        self._rebuild_slicer_bar()
        self.controls_panel.set_spec(self.spec)
        self._apply_plot_type()
        self.refresh_plot()
        self.fit_scale()

    def _rebuild_slicer_bar(self):
        """按新变量的额外维重建切片器栏（Panoply 式每维一行）。"""
        if self.slicer_bar is None:
            return
        parent = self.slicer_bar.parent()
        if parent is None:
            return
        # 从布局移除旧栏
        old = self.slicer_bar
        old.setParent(None)
        old.deleteLater()
        new_bar = self._build_slicer_bar()
        self.slicer_bar = new_bar
        if new_bar is not None:
            # 插回 time_bar 之后
            central = self.centralWidget()
            outer = central.layout()
            idx = outer.indexOf(self.time_bar) + 1
            outer.insertWidget(idx, new_bar)

    def fit_scale(self):
        """根据当前时次数据计算 min/max 并锁定（fit 按钮/打开/切换变量时调用）。

        切换时次不会自动调用，以便对比不同时次的差异。
        只对当前切片后的数据计算，避免大文件全量 .values 导致 OOM。
        """
        try:
            import numpy as np
            da = self.dataset[self.var_name]
            # 与 refresh_plot 相同的切片逻辑：Hovmöller/一维时序不切片
            if not _is_hovmoller(da) and da.ndim > 1:
                time_name = next((d for d in da.dims if "time" in d.lower()), None)
                if time_name is not None and self.time_strings:
                    idx = max(0, min(self._time_index, len(self.time_strings) - 1))
                    da = da.isel({time_name: idx})
            da = self._apply_extra_dims(da)
            values = np.asarray(da.values)
            finite = values[np.isfinite(values)]
            if finite.size == 0:
                return
            self.spec.level_min = float(np.min(finite))
            self.spec.level_max = float(np.max(finite))
            self.controls_panel._sync_from_spec()
            self.refresh_plot()
            self.status.showMessage(
                f"已适配范围：{self.spec.level_min:.4g} — {self.spec.level_max:.4g}")
        except Exception as exc:
            self.status.showMessage(f"适配失败：{exc}")

    # ---------- 时间选择 ----------
    def _set_anim_speed(self, ms: int, label: str):
        self._anim_timer.setInterval(ms)
        self.speed_btn.setText(label)
        self.status.showMessage(f"动画速度：{label}")

    def _sync_time_widgets(self):
        self._reentrant = True
        try:
            idx = max(0, min(self._time_index, len(self.time_strings) - 1)) if self.time_strings else 0
            self.slider.setValue(idx)
            self.time_spin.setValue(idx + 1)
            if self.time_combo.count():
                self.time_combo.setCurrentIndex(idx)
            if self.time_strings:
                self.time_label.setText(f"时次 {idx + 1} / {len(self.time_strings)}")
        finally:
            self._reentrant = False

    def _on_time_changed(self, index: int):
        if self._reentrant:
            return
        self._time_index = index
        self._sync_time_widgets()
        self.refresh_plot()

    def _on_spin_time(self, value: int):
        if self._reentrant:
            return
        self._on_time_changed(value - 1)

    def _on_combo_time(self, index: int):
        if self._reentrant or index < 0:
            return
        self._on_time_changed(index)

    def _on_slider(self, value: int):
        if self._reentrant:
            return
        self._on_time_changed(value)

    def _step_time(self, delta: int):
        n = len(self.time_strings)
        if n == 0:
            return
        new_idx = max(0, min(self._time_index + delta, n - 1))
        if new_idx != self._time_index:
            self._on_time_changed(new_idx)

    # ---------- 额外维度切片器（Panoply 式） ----------
    def _on_slicer_spin(self, ii, value):
        if self._reentrant or ii >= len(self._extra_dims):
            return
        n = len(self._extra_dims[ii][1])
        idx = max(0, min(value - 1, n - 1))
        if idx != self._extra_indices[ii]:
            self._extra_indices[ii] = idx
            self._sync_slicers()
            self.refresh_plot()

    def _on_slicer_combo(self, ii, index):
        if self._reentrant or ii >= len(self._extra_dims) or index < 0:
            return
        if index != self._extra_indices[ii]:
            self._extra_indices[ii] = index
            self._sync_slicers()
            self.refresh_plot()

    def _sync_slicers(self):
        self._reentrant = True
        try:
            for i in range(len(self._extra_dims)):
                self._slicer_spins[i].setValue(self._extra_indices[i] + 1)
                self._slicer_combos[i].setCurrentIndex(self._extra_indices[i])
        finally:
            self._reentrant = False

    def _apply_extra_dims(self, da):
        """把所有额外维切片应用到数据（时间切片后）。"""
        for i, (dim, _) in enumerate(self._extra_dims):
            if dim in da.dims:
                idx = max(0, min(self._extra_indices[i], len(self._extra_dims[i][1]) - 1))
                da = da.isel({dim: idx})
        return da

    # ---------- 动画播放（M2-A6） ----------
    def _on_play_toggled(self, checked: bool):
        if checked:
            if len(self.time_strings) > 1:
                self._anim_timer.start()
        else:
            self._anim_timer.stop()

    def _anim_step(self):
        n = len(self.time_strings)
        if n <= 1:
            self._anim_timer.stop()
            self.play.setChecked(False)
            return
        next_idx = self._time_index + 1
        if next_idx >= n:
            next_idx = 0  # 循环播放
        self._on_time_changed(next_idx)

    def _export_csv(self):
        """导出当前变量数据为 CSV（M2-D3）。"""
        from PySide6.QtWidgets import QFileDialog
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "导出数据", f"{self.var_name}.csv",
                                              "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            da = self.dataset[self.var_name]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                dims = list(da.dims)
                writer.writerow(dims + ["value"])
                series = da.to_series()  # MultiIndex 序列
                for idx, val in series.items():
                    keys = list(idx) if isinstance(idx, tuple) else [idx]
                    writer.writerow(keys + [float(val)])
            self.status.showMessage(f"已导出：{path}")
        except Exception as exc:
            self.status.showMessage(f"导出失败：{exc}")

    def _export_animation(self):
        """逐时次渲染并合成 GIF 动画（M3-F2）。"""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出动画", f"{self.var_name}.gif",
                                              "GIF 动画 (*.gif)")
        if not path:
            return
        n = len(self.time_strings)
        if n < 2:
            self.status.showMessage("时间维不足，无法导出动画")
            return
        self.status.showMessage("正在导出动画…")
        frames = []
        original_idx = self._time_index
        self.setEnabled(False)  # 导出期间锁定界面，防并发误操作
        try:
            import io
            from PIL import Image
            for idx in range(n):
                self._on_time_changed(idx)
                buf = io.BytesIO()
                self.figure.savefig(buf, format="png", dpi=80)
                buf.seek(0)
                frames.append(Image.open(buf).convert("RGB").copy())
                buf.close()
            frames[0].save(path, save_all=True, append_images=frames[1:],
                           duration=250, loop=0)
            self.status.showMessage(f"已导出动画：{path}")
        except Exception as exc:
            self.status.showMessage(f"导出失败：{exc}")
        finally:
            self.setEnabled(True)
            # 异常/完成都恢复原始时次
            if self._time_index != original_idx:
                self._on_time_changed(original_idx)

    # ---------- 渲染 ----------
    def _attach_aux_coords(self, da):
        """把 Dataset 层的 2D 辅助经纬度坐标 attach 到数据上（若未挂 coords）。

        curvilinear 文件里 lon/lat 可能是 data_vars（未 set_coords），此时
        da.coords 里没有它们，渲染层的 _aux_lon_lat 检测不到 → 会误判 contour。
        这里统一从 Dataset 补齐，保证渲染与类型判定看到辅助坐标。
        """
        from ncviewer.core.dataset import find_aux_lonlat
        if self.dataset is None:
            return da
        found = find_aux_lonlat(self.dataset, self.var_name)
        if found is None:
            return da
        lonv, latv = found
        missing = [c for c in (lonv, latv) if c not in da.coords]
        if missing:
            da = da.assign_coords({c: self.dataset[c] for c in missing})
        return da

    def refresh_plot(self):
        """统一重绘入口：时间滑块/控件/层次/变量切换四条路径都走这里。"""
        self.figure.clear()
        da = self.dataset[self.var_name]
        # Hovmöller 保留完整时间轴；其它带时间维且非一维时序的数据切到当前时次
        # （1D 时间序列变量直接画完整折线，不切片，避免降成 0 维标量）
        if not _is_hovmoller(da) and da.ndim > 1:
            time_name = next((d for d in da.dims if "time" in d.lower()), None)
            if time_name is not None and self.time_strings:
                idx = max(0, min(self._time_index, len(self.time_strings) - 1))
                da = da.isel({time_name: idx})
        da = self._apply_extra_dims(da)
        da = self._attach_aux_coords(da)
        try:
            render(da, self.spec, self.figure)
            self.canvas.draw()
            self._fill_data_table(da)
            self._fill_meta()
            self.status.showMessage(f"{self.var_name}：{self.spec.plot_type}")
        except Exception as exc:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"绘图失败：{exc}", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            self.canvas.draw()
            self.status.showMessage(f"绘图失败：{exc}")

    def _fill_data_table(self, da):
        """查看数据视图：把当前切片填充进表格。

        行 = Y 轴（lat/y 或第二维），列 = X 轴（lon/x 或第一维），
        表头用真实坐标值（与 Panoply View Data 一致）。超大维度截断到 200。
        """
        import numpy as np
        arr = np.asarray(da.values)
        if arr.ndim == 0:
            # 0 维标量（理论上被 refresh_plot 避免，仍做保护）
            self.data_table.clear()
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            self.table_info.setText("标量值：" + str(float(arr)))
            return
        while arr.ndim > 2:
            arr = arr[0]
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)

        # 确定行/列坐标（与渲染视角一致）
        def coord_values(name):
            if name in da.coords and name in da.dims:
                return [str(v) for v in da[name].values]
            if name in da.dims:
                return [str(i) for i in range(len(da[name]))]
            return [str(i) for i in range(arr.shape[0] if name == "index" else 0)] or ["—"]

        row_name = next((d for d in da.dims if d.lower() in {"lat", "latitude", "y"}), None)
        col_name = next((d for d in da.dims if d.lower() in {"lon", "longitude", "x"}), None)
        if da.ndim >= 2:
            if row_name is None:
                row_name = da.dims[-2]
            if col_name is None:
                col_name = da.dims[-1]
            row_labels = coord_values(row_name)
            col_labels = coord_values(col_name)
        else:
            row_name = da.dims[0] if da.dims else "index"
            col_name = None
            row_labels = coord_values(row_name)
            col_labels = ["值"]

        self._row_name = row_name
        self._col_name = col_name
        self._last_arr = arr
        self._last_row_labels = row_labels
        self._last_col_labels = col_labels

        # 维度标注（Panoply 式：行=Y 轴维度名，列=X 轴维度名）
        row_label = {"lat": "纬度", "latitude": "纬度", "y": "Y",
                     "lon": "经度", "longitude": "经度", "x": "X"}.get(row_name, row_name)
        col_label = {"lon": "经度", "longitude": "经度", "x": "X",
                     "lat": "纬度", "latitude": "纬度", "y": "Y"}.get(col_name or "", col_name or "")
        if col_name:
            self.table_info.setText(
                f"行：{row_name}（{row_label}，{len(row_labels)} 个值）    "
                f"列：{col_name}（{col_label}，{len(col_labels)} 个值）")
        else:
            self.table_info.setText(f"行：{row_name}（{row_label}，{len(row_labels)} 个值）")

        self._refill_data_table()

    def _refill_data_table(self):
        """按当前数字格式重填表格数据（格式下拉切换时调用）。

        数字右对齐等宽（科研表格惯例，小数点对齐）；不截断，显示全量。
        """
        arr = getattr(self, "_last_arr", None)
        if arr is None:
            return
        fmt = self.data_format_combo.currentText()
        rows = arr.shape[0]
        cols = arr.shape[1]
        self.data_table.clear()
        self.data_table.setRowCount(rows)
        self.data_table.setColumnCount(cols)
        self.data_table.setHorizontalHeaderLabels(self._last_col_labels[:cols])
        self.data_table.setVerticalHeaderLabels(self._last_row_labels[:rows])
        font = self.data_table.font()
        font.setFamily("Consolas, Courier New, monospace")
        for i in range(rows):
            for j in range(cols):
                try:
                    v = float(arr[i, j])
                    item = QTableWidgetItem(fmt % v)
                except Exception:
                    item = QTableWidgetItem("—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.data_table.setItem(i, j, item)
        self.data_table.resizeColumnsToContents()

    def _fill_meta(self):
        self.meta_view.setHtml(cdl_html(self.dataset, self.var_name))

    def _export_png(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出图像", f"{self.var_name}.png", "PNG 图像 (*.png)")
        if path:
            self.figure.savefig(path, dpi=150)
            self.status.showMessage(f"已导出：{path}")

    def closeEvent(self, event):
        if self._anim_timer.isActive():
            self._anim_timer.stop()  # 先停动画定时器，防止访问已销毁控件
        self.canvas.close()
        super().closeEvent(event)


def _ds_name(ds) -> str:
    """取数据集显示名（文件 base 名）。"""
    import os
    src = ds.attrs.get("_ncviewer_source_path")
    if src:
        return os.path.basename(str(src))
    return ds.attrs.get("title") or "数据集"


class CombinePlotWindow(QMainWindow):
    """合并绘图窗口（M2-B5）：多个变量在同一个 Figure 上以子图网格显示。

    每个变量使用自己的默认 PlotSpec；时间联动：共享同一时间滑块。
    """

    def __init__(self, var_specs: list, parent=None):
        """var_specs: [(dataset, var_name), ...]"""
        super().__init__(parent)
        self.var_specs = var_specs
        self.specs = [spec_from_defaults(v) for _, v in var_specs]
        # 控制面板接口：主 spec = 第一个变量的 spec（矢量参数存在这里）
        self.spec = self.specs[0]
        self.dataset = var_specs[0][0]
        self.var_name = var_specs[0][1]
        self.time_strings = _time_strings(var_specs[0][0], var_specs[0][1])
        self._time_index = 0
        self._reentrant = False

        names = " + ".join(v.replace("_", " ") for _, v in var_specs)[:60]
        self.setWindowTitle(f"合并绘图：{names}")
        self.setWindowIcon(app_icon(48))
        # 宽扁默认尺寸：画布接近 2:1，匹配 PlateCarree 全图纵横比，减少上下留白
        self.resize(1400, 640)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # 共享时间栏
        bar = QWidget()
        blay = QHBoxLayout(bar)
        blay.setContentsMargins(4, 2, 4, 2)
        blay.setSpacing(6)
        self.time_label = QLabel("时次")
        self.time_label.setObjectName("timeValue")
        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, max(1, len(self.time_strings)))
        self.time_spin.setToolTip("时次序号（可手动输入）")
        self.time_spin.setFixedWidth(70)
        self.time_combo = _NoWheelCombo()
        self.time_combo.addItems(self.time_strings or ["—"])
        self.time_combo.setMinimumWidth(120)
        self.btn_prev = QToolButton()
        self.btn_prev.setIcon(step_left_icon(22))
        self.btn_prev.setFixedSize(34, 32)
        self.btn_next = QToolButton()
        self.btn_next.setIcon(step_right_icon(22))
        self.btn_next.setFixedSize(34, 32)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, max(0, len(self.time_strings) - 1))
        self.slider.setFixedHeight(22)
        for w in (self.time_label, self.time_spin, self.time_combo,
                  self.btn_prev, self.btn_next):
            blay.addWidget(w)
        blay.addWidget(self.slider, 1)
        outer.addWidget(bar)

        self.figure = Figure(figsize=(10, 5), dpi=100)  # 接近 2:1，匹配 PlateCarree 全图纵横比
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer.addWidget(self.canvas, 1)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        outer.addWidget(self.toolbar)
        self.setCentralWidget(central)
        self.status = self.statusBar()
        self.status.showMessage("合并绘图")

        # 右侧绘图设置面板（对齐单变量窗口：QDockWidget + PlotControlsPanel）
        self._build_dock()

        self.time_spin.valueChanged.connect(self._on_spin_time)
        self.time_combo.currentIndexChanged.connect(self._on_combo_time)
        self.slider.valueChanged.connect(self._on_slider)
        self.btn_prev.clicked.connect(lambda: self._step_time(-1))
        self.btn_next.clicked.connect(lambda: self._step_time(1))

        self.refresh_plot()

    def _build_dock(self):
        """右侧「绘图设置」停靠面板（与单变量 PlotWindow 同款）。"""
        from ncviewer.ui.plot_controls import PlotControlsPanel
        self.controls_panel = PlotControlsPanel(self)
        dock = QDockWidget("绘图设置", self)
        dock.setObjectName("plotControlsDock")
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setWidget(self.controls_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.controls_dock = dock
        # 合并绘图按矢量/多子图设置：矢量对 → 矢量组可用
        names = [v for _, v in self.var_specs]
        from ncviewer.plots.render import _vector_pair
        if _vector_pair(names) is not None and len(self.var_specs) == 2:
            self.spec.plot_type = "vector"
            self.controls_panel.set_plot_type("vector")
        else:
            self.controls_panel.set_plot_type(self.spec.plot_type)
        self.controls_panel._sync_from_spec()

    def fit_scale(self):
        """矢量图不适用数据范围适配（控制面板按钮调用）。"""
        self.status.showMessage("矢量场无需适配数据范围")

    def on_variable_combo_changed(self, idx):
        """合并窗口内不切换变量（多变量固定）。"""
        pass

    def _slice(self, ds, var_name):
        da = ds[var_name]
        time_name = next((d for d in da.dims if "time" in d.lower()), None)
        if time_name is not None and self.time_strings:
            idx = max(0, min(self._time_index, len(self.time_strings) - 1))
            da = da.isel({time_name: idx})
        # 补齐 2D 辅助经纬度坐标（data_vars 未挂 coords 的场景）
        from ncviewer.core.dataset import find_aux_lonlat
        found = find_aux_lonlat(ds, var_name)
        if found is not None:
            lonv, latv = found
            missing = [c for c in (lonv, latv) if c not in da.coords]
            if missing:
                da = da.assign_coords({c: ds[c] for c in missing})
        return da

    def refresh_plot(self):
        from ncviewer.plots.render import _projection, _vector_pair, render, render_vector
        self.figure.clear()
        # 矢量对（u/v 分量）：画单张箭头图而不是两个填色子图
        names = [v for _, v in self.var_specs]
        pair = _vector_pair(names)
        if pair is not None and len(self.var_specs) == 2:
            self._render_vector(pair, render_vector)
            self.canvas.draw()
            return
        n = len(self.var_specs)
        import math
        cols = min(n, 2)
        rows = math.ceil(n / cols)
        for i, ((ds, var_name), spec) in enumerate(zip(self.var_specs, self.specs)):
            da = self._slice(ds, var_name)
            # 子图模式下：地图需要投影轴，先创建带投影的子图再传入 render
            if spec.plot_type == "map" and not _is_hovmoller(da):
                ax = self.figure.add_subplot(rows, cols, i + 1,
                                             projection=_projection(spec))
            else:
                ax = self.figure.add_subplot(rows, cols, i + 1)
            try:
                render(da, spec, self.figure, ax=ax)
            except Exception as exc:
                ax.set_title(f"{var_name}：渲染失败")
                ax.text(0.5, 0.5, str(exc), ha="center", va="center",
                        transform=ax.transAxes, fontsize=8)
        self.figure.tight_layout()
        self.canvas.draw()

    def _render_vector(self, pair, render_vector):
        """把 u/v 分量画成矢量箭头图（单图，覆盖两个变量）。

        关键：u 和 v 可能来自**不同文件**（如 uwnd.mon.mean.nc / vwnd.mon.mean.nc），
        必须按变量名从各自的 var_specs 条目取对应 dataset，不能用第一个文件的 ds。
        使用控制面板绑定的 self.spec（保留用户调整的样式/间隔/粗细/参考值等）。
        """
        from ncviewer.plots.render import _projection
        un, vn = pair
        # 按变量名找到各自的数据集（u/v 可能在不同文件里）
        ds_u = next((ds for ds, v in self.var_specs if v == un), self.var_specs[0][0])
        ds_v = next((ds for ds, v in self.var_specs if v == vn), ds_u)
        # 用控制面板绑定的主 spec（矢量参数用户可调），切到当前时次
        spec = self.spec
        if spec.plot_type != "vector":
            spec.plot_type = "vector"
            self.controls_panel.set_plot_type("vector")
        u = self._slice(ds_u, un)
        v = self._slice(ds_v, vn)
        # 极区数据自动用极地投影（与单变量 PlotWindow 一致）
        proj = _auto_polar_projection(u)
        if proj:
            spec.projection = proj
        import xarray as xr
        ds_vec = xr.Dataset({"u": u, "v": v})
        try:
            ax = self.figure.add_subplot(111, projection=_projection(spec))
            render_vector(ds_vec, spec, self.figure, ax=ax)
            # 紧凑布局：让地图铺满画布（默认 matplotlib 边距过大）
            try:
                self.figure.subplots_adjust(left=0.05, right=0.97, top=0.95, bottom=0.05)
            except Exception:
                pass
            self.status.showMessage(f"矢量场：{un} + {vn}")
        except Exception as exc:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"矢量绘图失败：{exc}", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_axis_off()
            self.status.showMessage(f"矢量绘图失败：{exc}")

    def _sync_time_widgets(self):
        self._reentrant = True
        try:
            idx = max(0, min(self._time_index, len(self.time_strings) - 1)) if self.time_strings else 0
            self.slider.setValue(idx)
            self.time_spin.setValue(idx + 1)
            if self.time_combo.count():
                self.time_combo.setCurrentIndex(idx)
            if self.time_strings:
                self.time_label.setText(f"时次 {idx + 1} / {len(self.time_strings)}")
        finally:
            self._reentrant = False

    def _on_time_changed(self, index):
        if self._reentrant:
            return
        self._time_index = index
        self._sync_time_widgets()
        self.refresh_plot()

    def _on_spin_time(self, value):
        if not self._reentrant:
            self._on_time_changed(value - 1)

    def _on_combo_time(self, index):
        if not self._reentrant and index >= 0:
            self._on_time_changed(index)

    def _on_slider(self, value):
        if not self._reentrant:
            self._on_time_changed(value)

    def _step_time(self, delta):
        n = len(self.time_strings)
        if n == 0:
            return
        new_idx = max(0, min(self._time_index + delta, n - 1))
        if new_idx != self._time_index:
            self._on_time_changed(new_idx)

    def closeEvent(self, event):
        self.canvas.close()
        super().closeEvent(event)
