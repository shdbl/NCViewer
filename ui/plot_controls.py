"""绘图设置控制面板（Panoply 全量可设置项）。

面板分组（与 Panoply createControls 对齐）：
- 数组 ARRAYS：变量 / 切片信息
- 等值线 CONTOURS：级数 / min / max / fit / 样式(填充/线/两者) / 线色 / 线宽 / 标注开关 / 标注字号 / 标注颜色
- 网格 GRID：开关 / 间隔 / 线型
- 标签 LABELS：标题 / 副标题 / X / Y / 脚注左中右 / 标题字号 / 副标题字号 / 脚注字号 / 图上 min-max
- 地图投影 MAP：投影 / 中心经纬度 / 经纬度范围 / 重置全球
- 色标 SCALE：颜色表 / 对数刻度 / 透明度 / 显示色标
- 折线 STROKE：线型（折线图用）
- 矢量 VECTORS：箭头缩放 / 抽稀 / 颜色（矢量场用）
- 数据归一化：normalize 开关
- 重置按钮

交互纪律：
- 数字控件禁用鼠标滚轮。
- fit 按钮：点击才适配；切换时次不自动 fit（便于对比时次差异）。
"""
from __future__ import annotations

from dataclasses import fields

from PySide6.QtCore import QRect, Qt, QSize
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QStyledItemDelegate, QStyle, QToolButton,
    QVBoxLayout, QWidget,
)

from ncviewer.plots.spec import PlotSpec, spec_from_defaults

_PROJECTIONS = [
    ("等距圆柱（PlateCarree）", "PlateCarree"),
    ("罗宾逊（Robinson）", "Robinson"),
    ("摩尔魏特（Mollweide）", "Mollweide"),
    ("兰勃特等角圆锥（LambertConformal）", "LambertConformal"),
    ("北半球极射（NorthPolarStereo）", "NorthPolarStereo"),
    ("墨卡托（Mercator）", "Mercator"),
]
_PROJECTION_LABELS = {eng: label for label, eng in _PROJECTIONS}
_PROJECTION_ENGS = {label: eng for label, eng in _PROJECTIONS}


def _proj_label(eng: str) -> str:
    """英文投影名 → 带中文描述的显示名。"""
    return _PROJECTION_LABELS.get(eng, eng)


def _proj_eng(label: str) -> str:
    """下拉显示名 → 英文投影名（写回 spec）。"""
    return _PROJECTION_ENGS.get(label, label)
_COLORMAPS = [
    "RdYlBu", "RdYlBu_r", "viridis", "plasma", "inferno", "magma", "cividis",
    "turbo", "coolwarm", "coolwarm_r", "bwr", "seismic", "RdBu", "RdBu_r",
    "Blues", "Reds", "Greens", "Oranges", "Purples",
    "YlOrRd", "YlGnBu", "PuBu", "GnBu", "BuPu",
    "jet", "rainbow", "ocean", "terrain",
    "gist_earth", "cubehelix", "Spectral", "Spectral_r",
]
_LINE_COLORS = {"自动": None, "蓝": "C0", "红": "C3", "绿": "C2",
                "橙": "C1", "黑": "black", "灰": "gray"}
_LABEL_COLORS = {"黑": "black", "白": "white", "红": "red", "蓝": "blue",
                 "绿": "green", "橙": "orange", "深灰": "dimgray"}
_CONTOUR_STYLES = {"填充": "filled", "线": "lines", "填充+线": "both"}
_GRID_STYLES = {"实线": "solid", "虚线": "dashed", "点线": "dotted"}
_LINE_STYLES = {"实线 -": "-", "虚线 --": "--", "点划线 -.": "-.", "点线 :": ":"}
_VECTOR_COLORS = {"黑": "black", "蓝": "blue", "红": "red", "绿": "green",
                  "橙": "orange", "深灰": "dimgray", "紫": "purple"}
_VECTOR_STYLES = {"箭头": "ARROW", "上游点": "UPDOT", "不画": "NONE"}


class _CollapsibleGroup(QWidget):
    """PPT 侧边栏式折叠分组：标题行（含箭头）点击展开/折叠内容。

    无复选框；标题整行可点，展开显示 ▼ + 内容，折叠显示 ▶。
    保持 setEnabled 语义（转发给内容）。
    """

    def __init__(self, title: str, parent=None, collapsed: bool = False):
        super().__init__(parent)
        self._base_title = title
        self._content = None
        self._disabled = False
        self.setObjectName("collapseGroup")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._header = QToolButton()
        self._header.setObjectName("collapseHeader")
        self._header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._header.setText(title)
        self._header.setCheckable(True)
        self._header.setChecked(not collapsed)
        self._header.setArrowType(Qt.ArrowType.DownArrow if not collapsed
                                  else Qt.ArrowType.RightArrow)
        self._header.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
        self._header.clicked.connect(self._on_toggled)
        lay.addWidget(self._header)

        self._content_widget = QWidget()
        self._content_widget.setObjectName("collapseContent")
        lay.addWidget(self._content_widget)

        self._content_lay = QFormLayout(self._content_widget)
        self._content_lay.setContentsMargins(2, 4, 2, 6)
        self._content_lay.setSpacing(2)
        self._content_widget.setVisible(not collapsed)

    def _on_toggled(self, checked: bool):
        self._header.setArrowType(Qt.ArrowType.DownArrow if checked
                                  else Qt.ArrowType.RightArrow)
        self._content_widget.setVisible(checked)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._header.setEnabled(True)  # 标题始终可点，禁用只影响内容控件

    def set_group_enabled(self, enabled: bool, collapse_when_disabled: bool = True):
        """整组启用/禁用：禁用时标题和内容都变灰（标题不可点）。

        启用时保持展开；禁用时折叠内容并置灰。
        """
        self._disabled = not enabled
        self._header.setEnabled(enabled)
        self._header.setChecked(enabled)
        self._header.setArrowType(Qt.ArrowType.DownArrow if enabled
                                  else Qt.ArrowType.RightArrow)
        self._content_widget.setVisible(enabled)
        super().setEnabled(enabled)

    # ---- 对外接口（保持与 QGroupBox 兼容） ----
    def form(self) -> "QFormLayout":
        return self._content_lay

    def isChecked(self) -> bool:
        return self._header.isChecked()


def _make_collapsible(title: str, collapsed: bool = False):
    """创建可折叠分组，返回 (group, form)。form 为组内容区的 QFormLayout。"""
    group = _CollapsibleGroup(title, collapsed=collapsed)
    form = group.form()
    form.setContentsMargins(8, 6, 8, 4)
    form.setHorizontalSpacing(10)
    form.setVerticalSpacing(4)
    return group, form


class _NoWheelSpin(QSpinBox):
    """禁用鼠标滚轮的 QSpinBox（仅数字调节，防误触）。"""

    def wheelEvent(self, event):
        event.ignore()


class _NoWheelDoubleSpin(QDoubleSpinBox):
    """禁用鼠标滚轮的 QDoubleSpinBox。"""

    def wheelEvent(self, event):
        event.ignore()


class _NoWheelCombo(QComboBox):
    """禁用鼠标滚轮的 QComboBox（滚动页面时误切换选项）。"""

    def wheelEvent(self, event):
        event.ignore()


class _ColormapDelegate(QStyledItemDelegate):
    """下拉项左侧画色表渐变预览条（右侧保留名称文字）。"""

    _PREVIEW_W = 72   # 渐变条宽 px
    _PREVIEW_H = 16   # 渐变条高 px

    def paint(self, painter, option, index):
        from matplotlib import colormaps
        cmap_name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        cmap = None
        try:
            cmap = colormaps[cmap_name]
        except Exception:
            pass
        # 先画默认项（含选中高亮背景）
        super().paint(painter, option, index)
        if cmap is None:
            return
        # 在文字左侧画渐变条
        rect = option.rect
        bar = QRect(rect.left() + 6,
                    rect.top() + (rect.height() - _ColormapDelegate._PREVIEW_H) // 2,
                    _ColormapDelegate._PREVIEW_W, _ColormapDelegate._PREVIEW_H)
        grad = QLinearGradient(bar.left(), 0, bar.right(), 0)
        steps = 8
        for i in range(steps + 1):
            r, g, b, _ = cmap(i / steps)
            grad.setColorAt(i / steps, QColor(int(r * 255), int(g * 255), int(b * 255)))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#bcc8d4"))
        painter.setBrush(grad)
        painter.drawRoundedRect(bar, 3, 3)
        painter.restore()


def _make_colormap_preview_pixmap(cmap_name: str, w: int = 72, h: int = 16) -> QPixmap:
    """生成色表渐变预览图（供组合框按钮区显示当前选中色表）。"""
    from matplotlib import colormaps
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    try:
        cmap = colormaps[cmap_name]
        grad = QLinearGradient(0, 0, w, 0)
        steps = 8
        for i in range(steps + 1):
            r, g, b, _ = cmap(i / steps)
            grad.setColorAt(i / steps, QColor(int(r * 255), int(g * 255), int(b * 255)))
        p.setPen(QColor("#bcc8d4"))
        p.setBrush(grad)
        p.drawRoundedRect(0, 0, w - 1, h - 1, 3, 3)
    finally:
        p.end()
    return pm


class PlotControlsPanel(QWidget):
    """绘图设置面板：布局固定，控件按绘图类型启用/隐藏。"""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.spec: PlotSpec = window.spec
        self._updating = False
        self._build_ui()
        self._fill_variables()

    # ---------- UI ----------
    @staticmethod
    def _hbox(*widgets) -> QWidget:
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        for w in widgets:
            lay.addWidget(w)
        return box

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        scroll.setWidget(body)
        outer.addWidget(scroll)

        # ---- 数组（展开） ----
        arr_group, arr_form = _make_collapsible("数组")
        self.variable_combo = _NoWheelCombo()
        self.variable_combo.setToolTip("选择要绘制的变量")
        self.slice_label = QLabel("—")
        self.slice_label.setObjectName("dimLabel")
        arr_form.addRow("变量", self.variable_combo)
        arr_form.addRow("切片", self.slice_label)
        lay.addWidget(arr_group)

        # ---- 等值线 CONTOURS（展开） ----
        ctr_group, ctr_form = _make_collapsible("等值线")
        self.levels_spin = _NoWheelSpin()
        self.levels_spin.setRange(5, 50)
        self.levels_spin.setValue(20)
        self.levels_spin.setSuffix(" 级")
        self.level_min_spin = _NoWheelDoubleSpin()
        self.level_min_spin.setRange(-1e12, 1e12)
        self.level_min_spin.setDecimals(4)
        self.level_max_spin = _NoWheelDoubleSpin()
        self.level_max_spin.setRange(-1e12, 1e12)
        self.level_max_spin.setDecimals(4)
        self.fit_button = QPushButton("适配数据范围")
        self.fit_button.setToolTip("根据当前时次数据计算并锁定色标 min/max\n（切换时次不会自动适配，便于对比）")
        self.contour_style_combo = _NoWheelCombo()
        self.contour_style_combo.addItems(list(_CONTOUR_STYLES.keys()))
        self.line_color_combo = _NoWheelCombo()
        self.line_color_combo.addItems(list(_LINE_COLORS.keys()))
        self.line_width_spin = _NoWheelDoubleSpin()
        self.line_width_spin.setRange(0.2, 5.0)
        self.line_width_spin.setDecimals(1)
        self.line_width_spin.setSingleStep(0.2)
        self.line_width_spin.setValue(1.0)
        self.contour_labels_check = QCheckBox("在等值线上标注数值")
        self.label_size_spin = _NoWheelDoubleSpin()
        self.label_size_spin.setRange(5, 20)
        self.label_size_spin.setDecimals(1)
        self.label_size_spin.setValue(8.0)
        self.label_size_spin.setSuffix(" pt")
        self.label_color_combo = _NoWheelCombo()
        self.label_color_combo.addItems(list(_LABEL_COLORS.keys()))
        ctr_form.addRow("级数", self.levels_spin)
        ctr_form.addRow("最小值", self.level_min_spin)
        ctr_form.addRow("最大值", self.level_max_spin)
        ctr_form.addRow("", self.fit_button)
        ctr_form.addRow("样式", self.contour_style_combo)
        ctr_form.addRow("线色", self.line_color_combo)
        ctr_form.addRow("线宽", self.line_width_spin)
        ctr_form.addRow("", self.contour_labels_check)
        ctr_form.addRow("标注字号", self.label_size_spin)
        ctr_form.addRow("标注颜色", self.label_color_combo)
        lay.addWidget(ctr_group)

        # ---- 网格 GRID（默认折叠） ----
        self.grid_group, grid_form = _make_collapsible("网格", collapsed=True)
        self.grid_on_check = QCheckBox("显示经纬网格线")
        self.grid_interval_spin = _NoWheelDoubleSpin()
        self.grid_interval_spin.setRange(1, 90)
        self.grid_interval_spin.setDecimals(0)
        self.grid_interval_spin.setValue(30)
        self.grid_style_combo = _NoWheelCombo()
        self.grid_style_combo.addItems(list(_GRID_STYLES.keys()))
        grid_form.addRow("", self.grid_on_check)
        grid_form.addRow("网格间隔", self.grid_interval_spin)
        grid_form.addRow("线型", self.grid_style_combo)
        lay.addWidget(self.grid_group)

        # ---- 标签 LABELS（默认折叠） ----
        self.lbl_group, lbl_form = _make_collapsible("标签", collapsed=True)
        self.title_edit = QLineEdit()
        self.subtitle_edit = QLineEdit()
        self.xlabel_edit = QLineEdit()
        self.ylabel_edit = QLineEdit()
        self.footnote_left_edit = QLineEdit()
        self.footnote_center_edit = QLineEdit()
        self.footnote_right_edit = QLineEdit()
        self.title_size_spin = _NoWheelDoubleSpin()
        self.title_size_spin.setRange(8, 28)
        self.title_size_spin.setDecimals(1)
        self.title_size_spin.setValue(12.0)
        self.subtitle_size_spin = _NoWheelDoubleSpin()
        self.subtitle_size_spin.setRange(6, 24)
        self.subtitle_size_spin.setDecimals(1)
        self.subtitle_size_spin.setValue(10.0)
        self.footnote_size_spin = _NoWheelDoubleSpin()
        self.footnote_size_spin.setRange(5, 20)
        self.footnote_size_spin.setDecimals(1)
        self.footnote_size_spin.setValue(8.0)
        self.minmax_check = QCheckBox("图上标注数据 min-max")
        lbl_form.addRow("标题", self.title_edit)
        lbl_form.addRow("副标题", self.subtitle_edit)
        lbl_form.addRow("X 轴", self.xlabel_edit)
        lbl_form.addRow("Y 轴", self.ylabel_edit)
        lbl_form.addRow("脚注(左)", self.footnote_left_edit)
        lbl_form.addRow("脚注(中)", self.footnote_center_edit)
        lbl_form.addRow("脚注(右)", self.footnote_right_edit)
        lbl_form.addRow("标题字号", self.title_size_spin)
        lbl_form.addRow("副标题字号", self.subtitle_size_spin)
        lbl_form.addRow("脚注字号", self.footnote_size_spin)
        lbl_form.addRow("", self.minmax_check)
        lay.addWidget(self.lbl_group)

        # ---- 地图投影 MAP（展开） ----
        self.projection_group, proj_form = _make_collapsible("地图投影")
        self.projection_combo = _NoWheelCombo()
        self.projection_combo.addItems([label for label, _ in _PROJECTIONS])
        self.central_lon_spin = _NoWheelDoubleSpin()
        self.central_lon_spin.setRange(-360, 360)
        self.central_lon_spin.setDecimals(1)
        self.central_lon_spin.setSuffix("°")
        self.central_lat_spin = _NoWheelDoubleSpin()
        self.central_lat_spin.setRange(-90, 90)
        self.central_lat_spin.setDecimals(1)
        self.central_lat_spin.setSuffix("°")
        self.lon_min_spin = _NoWheelDoubleSpin()
        self.lon_min_spin.setRange(-360, 360)
        self.lon_min_spin.setDecimals(1)
        self.lon_min_spin.setSuffix("°")
        self.lon_max_spin = _NoWheelDoubleSpin()
        self.lon_max_spin.setRange(-360, 360)
        self.lon_max_spin.setDecimals(1)
        self.lon_max_spin.setSuffix("°")
        self.lat_min_spin = _NoWheelDoubleSpin()
        self.lat_min_spin.setRange(-90, 90)
        self.lat_min_spin.setDecimals(1)
        self.lat_min_spin.setSuffix("°")
        self.lat_max_spin = _NoWheelDoubleSpin()
        self.lat_max_spin.setRange(-90, 90)
        self.lat_max_spin.setDecimals(1)
        self.lat_max_spin.setSuffix("°")
        self.extent_reset_button = QPushButton("重置为全球范围")
        proj_form.addRow("投影", self.projection_combo)
        proj_form.addRow("中心经度", self.central_lon_spin)
        proj_form.addRow("中心纬度", self.central_lat_spin)
        proj_form.addRow("经度范围", self._hbox(self.lon_min_spin, self.lon_max_spin))
        proj_form.addRow("纬度范围", self._hbox(self.lat_min_spin, self.lat_max_spin))
        proj_form.addRow("", self.extent_reset_button)
        lay.addWidget(self.projection_group)

        # ---- 色标 SCALE（展开） ----
        self.cm_group, cm_form = _make_collapsible("色标")
        self.colormap_combo = _NoWheelCombo()
        self.colormap_combo.addItems(_COLORMAPS)
        # 下拉项显示渐变预览条 + 当前选中项按钮区显示色表缩略图
        self.colormap_combo.setItemDelegate(_ColormapDelegate(self.colormap_combo))
        self.colormap_combo.setIconSize(QSize(72, 16))
        for i, name in enumerate(_COLORMAPS):
            self.colormap_combo.setItemIcon(i, _make_colormap_preview_pixmap(name))
        self.log_scale_check = QCheckBox("对数刻度")
        self.alpha_spin = _NoWheelDoubleSpin()
        self.alpha_spin.setRange(0.1, 1.0)
        self.alpha_spin.setDecimals(2)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setValue(1.0)
        self.show_colorbar_check = QCheckBox("显示色标")
        self.normalize_check = QCheckBox("归一化到 0-100")
        cm_form.addRow("颜色表", self.colormap_combo)
        cm_form.addRow("", self.log_scale_check)
        cm_form.addRow("透明度", self.alpha_spin)
        cm_form.addRow("", self.show_colorbar_check)
        cm_form.addRow("", self.normalize_check)
        lay.addWidget(self.cm_group)

        # ---- 折线 STROKE（默认折叠，仅折线图）----
        self.line_group, line_form = _make_collapsible("折线", collapsed=True)
        self.line_style_combo = _NoWheelCombo()
        self.line_style_combo.addItems(list(_LINE_STYLES.keys()))
        line_form.addRow("线型", self.line_style_combo)
        lay.addWidget(self.line_group)

        # ---- 矢量 VECTORS（默认折叠，仅矢量场）----
        self.vector_group, vec_form = _make_collapsible("矢量", collapsed=True)
        self.vector_style_combo = _NoWheelCombo()
        self.vector_style_combo.addItems(list(_VECTOR_STYLES.keys()))
        self.vector_style_combo.setToolTip("箭头样式（对齐 Panoply）")
        self.vector_spacing_spin = _NoWheelSpin()
        self.vector_spacing_spin.setRange(25, 250)
        self.vector_spacing_spin.setSuffix(" %")
        self.vector_spacing_spin.setValue(100)
        self.vector_spacing_spin.setToolTip("箭头间隔（100%=自动；越大越疏，Panoply Spacing）")
        self.vector_weight_spin = _NoWheelSpin()
        self.vector_weight_spin.setRange(25, 400)
        self.vector_weight_spin.setSuffix(" %")
        self.vector_weight_spin.setValue(100)
        self.vector_weight_spin.setToolTip("箭头线粗（100%=默认，Panoply Weight）")
        self.vector_refvalue_spin = _NoWheelDoubleSpin()
        self.vector_refvalue_spin.setRange(0.1, 10000.0)
        self.vector_refvalue_spin.setDecimals(2)
        self.vector_refvalue_spin.setValue(10.0)
        self.vector_refvalue_spin.setToolTip("参考值：箭头长度的基准（Panoply Reference Value）")
        self.vector_scale_spin = _NoWheelDoubleSpin()
        self.vector_scale_spin.setRange(0.1, 10.0)
        self.vector_scale_spin.setDecimals(1)
        self.vector_scale_spin.setValue(1.0)
        self.vector_density_spin = _NoWheelSpin()
        self.vector_density_spin.setRange(1, 10)
        self.vector_density_spin.setValue(1)
        self.vector_color_combo = _NoWheelCombo()
        self.vector_color_combo.addItems(list(_VECTOR_COLORS.keys()))
        self.vector_sample_check = QCheckBox("显示参考箭头")
        self.vector_sample_check.setChecked(True)
        self.vector_sample_check.setToolTip("在图例位置显示参考值对应的箭头长度")
        vec_form.addRow("样式", self.vector_style_combo)
        vec_form.addRow("间隔", self.vector_spacing_spin)
        vec_form.addRow("线粗", self.vector_weight_spin)
        vec_form.addRow("参考值", self.vector_refvalue_spin)
        vec_form.addRow("箭头缩放", self.vector_scale_spin)
        vec_form.addRow("抽稀步长", self.vector_density_spin)
        vec_form.addRow("箭头颜色", self.vector_color_combo)
        vec_form.addRow("", self.vector_sample_check)
        lay.addWidget(self.vector_group)

        # ---- 重置 ----
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.setToolTip("恢复该变量的默认绘图设置")
        lay.addWidget(self.reset_button)

        lay.addStretch(1)
        self._attach()
        self._init_extent_spins()
        self._sync_from_spec()

    # ---------- 经纬度范围 ----------
    def _init_extent_spins(self):
        """从数据坐标读取实际经纬度范围，作为 spin 的默认显示值。

        spec 默认全 None（全图），但 spin 需要显示真实范围，否则用户看到
        0.0° 会被误导，且只改一个值时无法形成完整矩形。
        """
        ds = getattr(self.window, "dataset", None)
        if ds is None:
            return
        # 找第一个含经纬度坐标的变量
        import numpy as np
        lo, la = None, None
        for n in ds.coords:
            low = n.lower()
            if low in ("lon", "longitude", "x") and lo is None:
                lo = n
            if low in ("lat", "latitude", "y") and la is None:
                la = n
        try:
            if lo is not None and la is not None:
                lons, lats = ds[lo].values, ds[la].values
                self._extent_default = {
                    "lon_min": float(np.min(lons)), "lon_max": float(np.max(lons)),
                    "lat_min": float(np.min(lats)), "lat_max": float(np.max(lats)),
                }
                # blockSignals：仅设置显示值，不触发 _on_lon_min 写 spec
                for sp in (self.lon_min_spin, self.lon_max_spin,
                           self.lat_min_spin, self.lat_max_spin):
                    sp.blockSignals(True)
                self.lon_min_spin.setValue(self._extent_default["lon_min"])
                self.lon_max_spin.setValue(self._extent_default["lon_max"])
                self.lat_min_spin.setValue(self._extent_default["lat_min"])
                self.lat_max_spin.setValue(self._extent_default["lat_max"])
                for sp in (self.lon_min_spin, self.lon_max_spin,
                           self.lat_min_spin, self.lat_max_spin):
                    sp.blockSignals(False)
        except Exception:
            pass

    def _write_full_extent(self):
        """把四个范围 spin 的当前值一起写进 spec（保证形成完整矩形）。"""
        self.spec.lon_min = float(self.lon_min_spin.value())
        self.spec.lon_max = float(self.lon_max_spin.value())
        self.spec.lat_min = float(self.lat_min_spin.value())
        self.spec.lat_max = float(self.lat_max_spin.value())

    # ---------- 变量填充 ----------
    def _fill_variables(self):
        """填充可绘制的数据变量（排除纯坐标变量）。blockSignals 防触发回调。"""
        ds = getattr(self.window, "dataset", None)
        if ds is None:
            return
        self.variable_combo.blockSignals(True)
        try:
            self.variable_combo.clear()
            names = [n for n in ds.variables if n not in ds.coords]
            if not names:
                names = [n for n in ds.variables]
            self.variable_combo.addItems(names)
        finally:
            self.variable_combo.blockSignals(False)

    # ---------- 事件 ----------
    def _attach(self):
        self.variable_combo.currentIndexChanged.connect(self._on_variable)
        self.levels_spin.valueChanged.connect(self._on_levels)
        self.level_min_spin.valueChanged.connect(self._on_level_min)
        self.level_max_spin.valueChanged.connect(self._on_level_max)
        self.fit_button.clicked.connect(self._on_fit)
        self.contour_style_combo.currentTextChanged.connect(self._on_contour_style)
        self.line_color_combo.currentTextChanged.connect(self._on_line_color)
        self.line_width_spin.valueChanged.connect(self._on_line_width)
        self.contour_labels_check.toggled.connect(self._on_contour_labels)
        self.label_size_spin.valueChanged.connect(self._on_label_size)
        self.label_color_combo.currentTextChanged.connect(self._on_label_color)
        self.grid_on_check.toggled.connect(self._on_grid_on)
        self.grid_interval_spin.valueChanged.connect(self._on_grid_interval)
        self.grid_style_combo.currentTextChanged.connect(self._on_grid_style)
        self.title_edit.textChanged.connect(self._on_title)
        self.subtitle_edit.textChanged.connect(self._on_subtitle)
        self.xlabel_edit.textChanged.connect(self._on_xlabel)
        self.ylabel_edit.textChanged.connect(self._on_ylabel)
        self.footnote_left_edit.textChanged.connect(self._on_footnote_left)
        self.footnote_center_edit.textChanged.connect(self._on_footnote_center)
        self.footnote_right_edit.textChanged.connect(self._on_footnote_right)
        self.title_size_spin.valueChanged.connect(self._on_title_size)
        self.subtitle_size_spin.valueChanged.connect(self._on_subtitle_size)
        self.footnote_size_spin.valueChanged.connect(self._on_footnote_size)
        self.minmax_check.toggled.connect(self._on_minmax)
        self.projection_combo.currentTextChanged.connect(self._on_projection)
        self.central_lon_spin.valueChanged.connect(self._on_central_lon)
        self.central_lat_spin.valueChanged.connect(self._on_central_lat)
        self.lon_min_spin.valueChanged.connect(self._on_lon_min)
        self.lon_max_spin.valueChanged.connect(self._on_lon_max)
        self.lat_min_spin.valueChanged.connect(self._on_lat_min)
        self.lat_max_spin.valueChanged.connect(self._on_lat_max)
        self.extent_reset_button.clicked.connect(self._on_extent_reset)
        self.colormap_combo.currentTextChanged.connect(self._on_colormap)
        self.log_scale_check.toggled.connect(self._on_log_scale)
        self.alpha_spin.valueChanged.connect(self._on_alpha)
        self.show_colorbar_check.toggled.connect(self._on_show_colorbar)
        self.normalize_check.toggled.connect(self._on_normalize)
        self.line_style_combo.currentTextChanged.connect(self._on_line_style)
        self.vector_style_combo.currentTextChanged.connect(self._on_vector_style)
        self.vector_spacing_spin.valueChanged.connect(self._on_vector_spacing)
        self.vector_weight_spin.valueChanged.connect(self._on_vector_weight)
        self.vector_refvalue_spin.valueChanged.connect(self._on_vector_refvalue)
        self.vector_scale_spin.valueChanged.connect(self._on_vector_scale)
        self.vector_density_spin.valueChanged.connect(self._on_vector_density)
        self.vector_color_combo.currentTextChanged.connect(self._on_vector_color)
        self.vector_sample_check.toggled.connect(self._on_vector_sample)
        self.reset_button.clicked.connect(self._reset_spec)

    # ---- 写回 spec ----
    def _on_variable(self, _=0):
        if self._updating:
            return
        idx = self.variable_combo.currentIndex()
        if idx >= 0:
            self.window.on_variable_combo_changed(idx)

    def _on_levels(self, v):
        if not self._updating:
            self.spec.levels = int(v)
            self._refresh()

    def _on_level_min(self, v):
        if not self._updating:
            self.spec.level_min = float(v)
            self._refresh()

    def _on_level_max(self, v):
        if not self._updating:
            self.spec.level_max = float(v)
            self._refresh()

    def _on_fit(self):
        if self.window is not None:
            self.window.fit_scale()

    def _on_contour_style(self, text):
        if not self._updating:
            self.spec.contour_style = _CONTOUR_STYLES.get(text, "filled")
            self._refresh()

    def _on_line_color(self, text):
        if not self._updating:
            self.spec.line_color = _LINE_COLORS.get(text)
            self._refresh()

    def _on_line_width(self, v):
        if not self._updating:
            self.spec.line_width = float(v)
            self._refresh()

    def _on_contour_labels(self, checked):
        if not self._updating:
            self.spec.contour_labels = bool(checked)
            self._refresh()

    def _on_label_size(self, v):
        if not self._updating:
            self.spec.label_size = float(v)
            self._refresh()

    def _on_label_color(self, text):
        if not self._updating:
            self.spec.label_color = _LABEL_COLORS.get(text, "black")
            self._refresh()

    def _on_grid_on(self, checked):
        if not self._updating:
            self.spec.grid_on = bool(checked)
            self._refresh()

    def _on_grid_interval(self, v):
        if not self._updating:
            self.spec.grid_interval = float(v)
            self._refresh()

    def _on_grid_style(self, text):
        if not self._updating:
            self.spec.grid_line_style = _GRID_STYLES.get(text, "solid")
            self._refresh()

    def _on_title(self, text):
        if not self._updating:
            self.spec.title = text
            self._refresh()

    def _on_subtitle(self, text):
        if not self._updating:
            self.spec.subtitle = text
            self._refresh()

    def _on_xlabel(self, text):
        if not self._updating:
            self.spec.xlabel = text
            self._refresh()

    def _on_ylabel(self, text):
        if not self._updating:
            self.spec.ylabel = text
            self._refresh()

    def _on_footnote_left(self, text):
        if not self._updating:
            self.spec.footnote_left = text
            self._refresh()

    def _on_footnote_center(self, text):
        if not self._updating:
            self.spec.footnote_center = text
            self._refresh()

    def _on_footnote_right(self, text):
        if not self._updating:
            self.spec.footnote_right = text
            self._refresh()

    def _on_title_size(self, v):
        if not self._updating:
            self.spec.title_size = float(v)
            self._refresh()

    def _on_subtitle_size(self, v):
        if not self._updating:
            self.spec.subtitle_size = float(v)
            self._refresh()

    def _on_footnote_size(self, v):
        if not self._updating:
            self.spec.footnote_size = float(v)
            self._refresh()

    def _on_minmax(self, checked):
        if not self._updating:
            self.spec.show_minmax = bool(checked)
            self._refresh()

    def _on_projection(self, text):
        if not self._updating:
            self.spec.projection = _proj_eng(text)
            self._refresh()

    def _on_central_lon(self, v):
        if not self._updating:
            self.spec.central_lon = float(v)
            self._refresh()

    def _on_central_lat(self, v):
        if not self._updating:
            self.spec.central_lat = float(v)
            self._refresh()

    def _on_lon_min(self, v):
        if not self._updating:
            self._write_full_extent()
            self._refresh()

    def _on_lon_max(self, v):
        if not self._updating:
            self._write_full_extent()
            self._refresh()

    def _on_lat_min(self, v):
        if not self._updating:
            self._write_full_extent()
            self._refresh()

    def _on_lat_max(self, v):
        if not self._updating:
            self._write_full_extent()
            self._refresh()

    def _on_extent_reset(self):
        if not self._updating:
            self.spec.lon_min = None
            self.spec.lon_max = None
            self.spec.lat_min = None
            self.spec.lat_max = None
            # spin 恢复为数据默认范围（blockSignals 防止触发写回）
            d = getattr(self, "_extent_default", None)
            if d:
                for sp in (self.lon_min_spin, self.lon_max_spin,
                           self.lat_min_spin, self.lat_max_spin):
                    sp.blockSignals(True)
                self.lon_min_spin.setValue(d["lon_min"])
                self.lon_max_spin.setValue(d["lon_max"])
                self.lat_min_spin.setValue(d["lat_min"])
                self.lat_max_spin.setValue(d["lat_max"])
                for sp in (self.lon_min_spin, self.lon_max_spin,
                           self.lat_min_spin, self.lat_max_spin):
                    sp.blockSignals(False)
            self._refresh()

    def _on_colormap(self, text):
        if not self._updating:
            self.spec.colormap = text
            self._refresh()

    def _on_log_scale(self, checked):
        if self._updating:
            return
        if checked and self.window is not None:
            try:
                da = self.window.dataset[self.window.var_name]
                import numpy as np
                v = np.asarray(da.values)
                if np.nanmax(v) <= 0:
                    self.spec.log_scale = False
                    self.log_scale_check.blockSignals(True)
                    self.log_scale_check.setChecked(False)
                    self.log_scale_check.blockSignals(False)
                    self.window.status.showMessage("非正数据无法使用对数刻度，已自动回退")
                    return
            except Exception:
                pass
        self.spec.log_scale = bool(checked)
        self._refresh()

    def _on_alpha(self, v):
        if not self._updating:
            self.spec.alpha = float(v)
            self._refresh()

    def _on_show_colorbar(self, checked):
        if not self._updating:
            self.spec.show_colorbar = bool(checked)
            self._refresh()

    def _on_normalize(self, checked):
        if not self._updating:
            self.spec.normalize = bool(checked)
            self._refresh()

    def _on_line_style(self, text):
        if not self._updating:
            self.spec.line_style = _LINE_STYLES.get(text, "-")
            self._refresh()

    def _on_vector_scale(self, v):
        if not self._updating:
            self.spec.vector_scale = float(v)
            self._refresh()

    def _on_vector_style(self, text):
        if not self._updating:
            self.spec.vector_style = _VECTOR_STYLES.get(text, "ARROW")
            self._refresh()

    def _on_vector_spacing(self, v):
        if not self._updating:
            self.spec.vector_spacing = int(v)
            self._refresh()

    def _on_vector_weight(self, v):
        if not self._updating:
            self.spec.vector_weight = int(v)
            self._refresh()

    def _on_vector_refvalue(self, v):
        if not self._updating:
            self.spec.vector_refvalue = float(v)
            self._refresh()

    def _on_vector_sample(self, checked):
        if not self._updating:
            self.spec.vector_sample = bool(checked)
            self._refresh()

    def _on_vector_density(self, v):
        if not self._updating:
            self.spec.vector_density = int(v)
            self._refresh()

    def _on_vector_color(self, text):
        if not self._updating:
            self.spec.vector_color = _VECTOR_COLORS.get(text, "black")
            self._refresh()

    def _refresh(self):
        """写回 spec 后触发统一重绘（仅响应真实用户变更）。"""
        if self.window is not None:
            self.window.refresh_plot()

    # ---- 重置（原地赋值，保持引用一致） ----
    def _reset_spec(self):
        defaults = spec_from_defaults(self.spec.var_name or "变量")
        for f in fields(PlotSpec):
            setattr(self.spec, f.name, getattr(defaults, f.name))
        self._sync_from_spec()
        if self.window is not None:
            self.window.fit_scale()

    # ---- 从 spec 同步控件（blockSignals 防回环） ----
    def _sync_from_spec(self):
        self._updating = True
        try:
            s = self.spec
            idx = self.variable_combo.findText(s.var_name or "")
            if idx >= 0:
                self.variable_combo.setCurrentIndex(idx)
            self.levels_spin.setValue(int(s.levels) if s.levels else 20)
            if s.level_min is not None:
                self.level_min_spin.setValue(s.level_min)
            if s.level_max is not None:
                self.level_max_spin.setValue(s.level_max)
            self.contour_style_combo.setCurrentText(
                next((k for k, v in _CONTOUR_STYLES.items() if v == s.contour_style), "填充"))
            self.line_color_combo.setCurrentText(
                next((k for k, v in _LINE_COLORS.items() if v == s.line_color), "自动"))
            self.line_width_spin.setValue(getattr(s, "line_width", 1.0))
            self.contour_labels_check.setChecked(bool(s.contour_labels))
            self.label_size_spin.setValue(s.label_size)
            self.label_color_combo.setCurrentText(
                next((k for k, v in _LABEL_COLORS.items() if v == s.label_color), "黑"))
            self.grid_on_check.setChecked(bool(s.grid_on))
            if s.grid_interval is not None:
                self.grid_interval_spin.setValue(s.grid_interval)
            self.grid_style_combo.setCurrentText(
                next((k for k, v in _GRID_STYLES.items() if v == s.grid_line_style), "实线"))
            self.title_edit.setText(s.title)
            self.subtitle_edit.setText(s.subtitle)
            self.xlabel_edit.setText(s.xlabel)
            self.ylabel_edit.setText(s.ylabel)
            self.footnote_left_edit.setText(getattr(s, "footnote_left", ""))
            self.footnote_center_edit.setText(getattr(s, "footnote_center", ""))
            self.footnote_right_edit.setText(getattr(s, "footnote_right", ""))
            self.title_size_spin.setValue(getattr(s, "title_size", 12.0))
            self.subtitle_size_spin.setValue(getattr(s, "subtitle_size", 10.0))
            self.footnote_size_spin.setValue(getattr(s, "footnote_size", 8.0))
            self.minmax_check.setChecked(bool(getattr(s, "show_minmax", False)))
            self.projection_combo.setCurrentText(_proj_label(s.projection))
            self.central_lon_spin.setValue(s.central_lon)
            self.central_lat_spin.setValue(s.central_lat)
            d = getattr(self, "_extent_default", None) or {}
            if s.lon_min is not None:
                self.lon_min_spin.setValue(s.lon_min)
            elif "lon_min" in d:
                self.lon_min_spin.setValue(d["lon_min"])
            if s.lon_max is not None:
                self.lon_max_spin.setValue(s.lon_max)
            elif "lon_max" in d:
                self.lon_max_spin.setValue(d["lon_max"])
            if s.lat_min is not None:
                self.lat_min_spin.setValue(s.lat_min)
            elif "lat_min" in d:
                self.lat_min_spin.setValue(d["lat_min"])
            if s.lat_max is not None:
                self.lat_max_spin.setValue(s.lat_max)
            elif "lat_max" in d:
                self.lat_max_spin.setValue(d["lat_max"])
            self.colormap_combo.setCurrentText(s.colormap)
            self.log_scale_check.setChecked(bool(getattr(s, "log_scale", False)))
            self.alpha_spin.setValue(getattr(s, "alpha", 1.0))
            self.show_colorbar_check.setChecked(bool(s.show_colorbar))
            self.normalize_check.setChecked(bool(getattr(s, "normalize", False)))
            self.line_style_combo.setCurrentText(
                next((k for k, v in _LINE_STYLES.items() if v == getattr(s, "line_style", "-")), "实线 -"))
            self.vector_style_combo.setCurrentText(
                next((k for k, v in _VECTOR_STYLES.items() if v == getattr(s, "vector_style", "ARROW")), "箭头"))
            self.vector_spacing_spin.setValue(getattr(s, "vector_spacing", 100))
            self.vector_weight_spin.setValue(getattr(s, "vector_weight", 100))
            self.vector_refvalue_spin.setValue(getattr(s, "vector_refvalue", 10.0))
            self.vector_scale_spin.setValue(getattr(s, "vector_scale", 1.0))
            self.vector_density_spin.setValue(getattr(s, "vector_density", 1))
            self.vector_color_combo.setCurrentText(
                next((k for k, v in _VECTOR_COLORS.items() if v == getattr(s, "vector_color", "black")), "黑"))
            self.vector_sample_check.setChecked(bool(getattr(s, "vector_sample", True)))
        finally:
            self._updating = False

    # ---- 对外接口 ----
    def set_spec(self, spec: PlotSpec):
        """替换 spec 引用并同步控件（保持新引用）。"""
        self.spec = spec
        self._sync_from_spec()

    def set_plot_type(self, plot_type: str):
        """按绘图类型启用/禁用相关组。

        用不了的组折叠+置灰（标题也灰、不可点）；可用的组展开。
        适用性：
        - 投影/网格：仅地图（map）
        - 折线：仅折线图（line）
        - 矢量：仅矢量场（vector）
        - 等值线/标签/色标/数组：通用（始终可用）
        """
        is_map = plot_type == "map"
        is_line = plot_type == "line"
        is_vector = plot_type == "vector"
        self.projection_group.set_group_enabled(is_map)
        self.grid_group.set_group_enabled(is_map or is_vector)
        self.line_group.set_group_enabled(is_line)
        self.vector_group.set_group_enabled(is_vector)
        self.grid_on_check.setEnabled(is_map or is_vector)

    def update_slice_info(self, text: str):
        self.slice_label.setText(text)
