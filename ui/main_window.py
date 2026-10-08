"""主窗口（Panoply 范式）：工具栏 + 三标签页数据浏览器 + 状态栏。

- 工具栏：创建绘图 | 合并绘图 | 打开数据集 | (glue) | 移除一个 | 移除全部 | (glue) | 隐藏信息
  （使用 Panoply 官方 PNG 图标，36px）。
- 数据浏览器：左侧三列表格树（名称|长名称|类型）+ 底部 Show 过滤器；
  右侧元数据面板（概览/原始信息 CDL）。
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFileDialog, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter,
    QToolBar, QTreeWidget, QVBoxLayout, QWidget,
)

from ncviewer.core.dataset import describe_variables, open_dataset
from ncviewer.ui.datatree import build_tree, item_payload
from ncviewer.ui.plot_controls import _NoWheelCombo
from ncviewer.ui.icons import (
    app_icon, chart_icon, layers_icon, open_icon, panel_right_icon,
    trash_all_icon, trash_icon,
)
from ncviewer.ui.metadata_panel import MetadataPanel
from ncviewer.ui.plot_window import CombinePlotWindow, PlotWindow
from ncviewer.ui.style import apply_app_style


class MainWindow(QMainWindow):
    """NCViewer 主窗口。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.datasets: list = []           # 已打开的 xarray.Dataset（供测试/外部访问）
        self.dataset_paths: dict = {}      # id(ds) -> path
        self._plots: list = []
        self.settings = QSettings("NCViewer", "NCViewer")
        self._recent_files = self.settings.value("最近打开", []) or []
        self._recent_actions: list = []
        app = QApplication.instance()
        if app is not None:
            apply_app_style(app)

        self.setWindowTitle("NCViewer")
        self.setWindowIcon(app_icon(64))
        self.resize(1180, 720)
        geo = self.settings.value("窗口位置")
        if geo:
            self.restoreGeometry(geo)
        self._build_toolbar()
        self._build_menu()
        self._build_body()
        self.statusBar().showMessage("请打开 NetCDF 数据集")

    # ---------- 工具栏（现代 SVG 线性图标，紧凑） ----------
    def _build_toolbar(self):
        tb = QToolBar("主工具栏")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setContentsMargins(4, 2, 4, 2)
        self.addToolBar(tb)

        self.create_plot_action = QAction(chart_icon(20), "创建绘图", self)
        self.create_plot_action.setToolTip("为选中的变量创建绘图")
        self.create_plot_action.triggered.connect(self._on_create_plot)
        tb.addAction(self.create_plot_action)

        self.combine_plot_action = QAction(layers_icon(20), "合并绘图", self)
        self.combine_plot_action.setToolTip("把多个变量合并到同一绘图（需先选中多个变量）")
        self.combine_plot_action.setEnabled(False)
        self.combine_plot_action.triggered.connect(self._on_combine_plot)
        tb.addAction(self.combine_plot_action)

        self.open_action = QAction(open_icon(20), "打开数据集", self)
        self.open_action.setToolTip("打开本地 NetCDF 文件")
        self.open_action.triggered.connect(self._on_open)
        tb.addAction(self.open_action)

        tb.addSeparator()

        self.remove_one_action = QAction(trash_icon(20), "移除一个", self)
        self.remove_one_action.setToolTip("从数据浏览器移除选中的数据集")
        self.remove_one_action.setEnabled(False)
        self.remove_one_action.triggered.connect(self._on_remove_one)
        tb.addAction(self.remove_one_action)

        self.remove_all_action = QAction(trash_all_icon(20), "移除全部", self)
        self.remove_all_action.setToolTip("清空数据浏览器")
        self.remove_all_action.setEnabled(False)
        self.remove_all_action.triggered.connect(self._on_remove_all)
        tb.addAction(self.remove_all_action)

        tb.addSeparator()

        self.toggle_info_action = QAction(panel_right_icon(20), "隐藏信息", self)
        self.toggle_info_action.setToolTip("显示/隐藏右侧元数据面板")
        self.toggle_info_action.triggered.connect(self._on_toggle_info)
        tb.addAction(self.toggle_info_action)

    def _build_menu(self):
        mbar = self.menuBar()
        file_menu = mbar.addMenu("文件")
        act_open = QAction("打开数据集…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._on_open)
        file_menu.addAction(act_open)
        # 最近打开（M3-E1）
        self.recent_menu = file_menu.addMenu("最近打开")
        self._rebuild_recent_menu()
        act_quit = QAction("退出", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = mbar.addMenu("视图")
        act_info = QAction("元数据面板", self)
        act_info.setCheckable(True)
        act_info.setChecked(True)
        act_info.triggered.connect(lambda on: self.info_panel.setVisible(on))
        view_menu.addAction(act_info)

        help_menu = mbar.addMenu("帮助")
        act_about = QAction("关于 NCViewer", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    # ---------- 主体 ----------
    def _build_body(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左：数据浏览器（Show 过滤器 + 树 + 空状态）
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(2)

        # 过滤器置顶（PyCharm/VS Code 通用模式）
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(4, 2, 4, 2)
        show_label = QLabel("显示:")
        show_label.setObjectName("dimLabel")
        self.filter_combo = _NoWheelCombo()
        self.filter_combo.addItems(["所有变量", "可绘图变量"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(show_label)
        filter_row.addWidget(self.filter_combo, 1)
        left_lay.addLayout(filter_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "长名称", "类型"])
        # 多选支持（Ctrl/Shift 多选变量 → 合并绘图；Panoply 同款交互）
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # 拖拽打开：接受 .nc 文件拖入
        self.tree.setAcceptDrops(True)
        self.setAcceptDrops(True)
        # 列宽交互式调整 + QSettings 记忆
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setColumnWidth(0, self.settings.value("树列0宽度", 180, int))
        self.tree.setColumnWidth(1, self.settings.value("树列1宽度", 210, int))
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_context_menu)
        left_lay.addWidget(self.tree)

        # 空状态提示（图标 + 文字 + 打开按钮）
        self.empty_state = QWidget()
        self.empty_state.setObjectName("emptyState")
        es_lay = QVBoxLayout(self.empty_state)
        es_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_lay.setSpacing(12)
        from ncviewer.ui.icons import dataset_icon
        es_icon = QLabel()
        es_icon.setPixmap(dataset_icon(64).pixmap(64, 64))
        es_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_lay.addWidget(es_icon)
        es_text = QLabel("请打开 NetCDF 数据集")
        es_text.setObjectName("emptyState")
        es_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_lay.addWidget(es_text)
        es_btn = QPushButton("打开数据集…")
        es_btn.setDefault(True)
        es_btn.setFixedWidth(140)
        es_btn.clicked.connect(self._on_open)
        es_lay.addWidget(es_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        es_hint = QLabel("或按 Ctrl+O")
        es_hint.setObjectName("dimLabel")
        es_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_lay.addWidget(es_hint)
        left_lay.addWidget(self.empty_state, 1)

        splitter.addWidget(left)

        # 右：元数据面板
        self.metadata = MetadataPanel()
        self.info_panel = self.metadata
        splitter.addWidget(self.metadata)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([680, 500])
        self.setCentralWidget(splitter)

    def _tree_context_menu(self, pos):
        """数据树右键菜单：低频操作下沉（移除/清空）。"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        item = self.tree.itemAt(pos)
        if item is not None and item_payload(item).get("kind") == "dataset":
            act_rm = menu.addAction("移除此数据集")
            act_rm.triggered.connect(self._on_remove_one)
            menu.addSeparator()
        act_all = menu.addAction("清空数据浏览器")
        act_all.triggered.connect(self._on_remove_all)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ---------- 动作 ----------
    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开数据文件", "",
            "NetCDF/GRIB 文件 (*.nc *.nc4 *.grb *.grib *.grb2 *.grib2);;所有文件 (*)")
        if path:
            self.open_file(path)

    def _rebuild_recent_menu(self):
        self.recent_menu.clear()
        self._recent_actions.clear()
        for path in self._recent_files:
            act = QAction(path, self)
            act.triggered.connect(lambda _=False, p=path: self.open_file(p))
            self.recent_menu.addAction(act)
            self._recent_actions.append(act)
        if not self._recent_files:
            empty = QAction("（无）", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)

    def _remember_recent(self, path: str):
        lst = [p for p in self._recent_files if p != path]
        lst.insert(0, path)
        self._recent_files = lst[:8]
        self.settings.setValue("最近打开", self._recent_files)
        self._rebuild_recent_menu()

    def open_file(self, path: str) -> bool:
        """打开本地 .nc 文件，构建两级树，更新元数据。"""
        try:
            ds = open_dataset(path)
        except Exception as exc:
            QMessageBox.warning(self, "打开失败", str(exc))
            return False
        if any(d is ds for d in self.datasets):
            return True
        # 追加打开：不清空树，多数据集并存
        self.datasets.append(ds)
        self.dataset_paths[id(ds)] = str(path)
        variables = describe_variables(ds)
        build_tree(self.tree, ds, path, variables, clear=len(self.datasets) == 1)
        self.metadata.set_dataset(ds)
        self.empty_state.hide()
        self.statusBar().showMessage(f"已打开：{os.path.basename(str(path))}")
        self._refresh_actions()
        self._remember_recent(str(path))
        return True

    def new_plot(self, dataset, var_name: str) -> PlotWindow:
        """为变量创建绘图窗口并显示。dataset 可以是 xarray.Dataset 或文件路径字符串。"""
        ds = dataset
        if isinstance(dataset, str):
            ds = self._find_ds(dataset)
            if ds is None:
                try:
                    ds = open_dataset(dataset)
                except Exception as exc:
                    QMessageBox.warning(self, "打开失败", str(exc))
                    return None
        plot = PlotWindow(ds, var_name)
        plot.show()
        self._plots.append(plot)
        return plot

    def _on_create_plot(self):
        item = self.tree.currentItem()
        if item is None:
            return
        payload = item_payload(item)
        if payload.get("kind") != "variable":
            return
        ds = self._find_ds(payload.get("dataset"))
        if ds is not None:
            self.new_plot(ds, payload["var_name"])

    def _on_combine_plot(self):
        """合并绘图：把选中变量在同一个窗口用多个子图叠加显示（M2-B5）。"""
        items = self.tree.selectedItems()
        vars_ = []
        for it in items:
            payload = item_payload(it)
            if payload.get("kind") == "variable":
                ds = self._find_ds(payload.get("dataset"))
                if ds is not None:
                    vars_.append((ds, payload["var_name"]))
        if len(vars_) < 2:
            QMessageBox.information(self, "合并绘图",
                                    "请先在树中按住 Ctrl 选中多个变量，再点「合并绘图」。")
            return
        plot = CombinePlotWindow(vars_, parent=self)
        plot.show()
        self._plots.append(plot)

    def _on_double_clicked(self, item, _col):
        payload = item_payload(item)
        if payload.get("kind") == "variable":
            ds = self._find_ds(payload.get("dataset"))
            if ds is not None:
                self.new_plot(ds, payload["var_name"])

    def _on_selection_changed(self):
        item = self.tree.currentItem()
        if item is None:
            self._refresh_actions()
            return
        payload = item_payload(item)
        if payload.get("kind") == "dataset":
            # 数据集节点 payload 用 path 定位
            ds = self._find_ds(payload.get("path"))
            if ds is not None:
                self.metadata.show_item(ds)
            self._refresh_actions()
            return
        ds = self._find_ds(payload.get("dataset"))
        if ds is None:
            self._refresh_actions()
            return
        if payload.get("kind") == "variable":
            self.metadata.show_item(ds, payload.get("var_name"))
        self._refresh_actions()

    def _find_ds(self, path: str | None):
        if path is None:
            return None
        for ds in self.datasets:
            if self.dataset_paths.get(id(ds)) == str(path):
                return ds
        return None

    def _on_filter_changed(self, _idx=0):
        # 过滤逻辑：可绘图变量 = 数据变量（非纯坐标变量）
        mode = self.filter_combo.currentText()
        drawable_names = set()
        for ds in self.datasets:
            for n in ds.data_vars:
                drawable_names.add(n)
        for i in range(self.tree.topLevelItemCount()):
            ds_item = self.tree.topLevelItem(i)
            for j in range(ds_item.childCount()):
                vi = ds_item.child(j)
                payload = item_payload(vi)
                if payload.get("kind") != "variable":
                    continue
                var_name = payload.get("var_name", "")
                vi.setHidden(mode == "可绘图变量" and var_name not in drawable_names)

    def _var_dims(self, var_name: str) -> list:
        for ds in self.datasets:
            if var_name in ds.variables:
                return list(ds[var_name].dims)
        return []

    def _on_remove_one(self):
        item = self.tree.currentItem()
        if item is None:
            return
        payload = item_payload(item)
        path = payload.get("dataset") if payload.get("kind") == "variable" else payload.get("path")
        for ds in self.datasets:
            if self.dataset_paths.get(id(ds)) == str(path):
                self.datasets.remove(ds)
                del self.dataset_paths[id(ds)]
                break
        self._rebuild_tree()

    def _on_remove_all(self):
        self.datasets.clear()
        self.dataset_paths.clear()
        self.tree.clear()
        self.metadata.clear_panel()
        self.empty_state.show()
        self.statusBar().showMessage("已清空")
        self._refresh_actions()

    def _rebuild_tree(self):
        self.tree.clear()
        if not self.datasets:
            self.empty_state.show()
        for ds in self.datasets:
            path = self.dataset_paths.get(id(ds), "")
            build_tree(self.tree, ds, path, describe_variables(ds))
        self._refresh_actions()

    def _on_toggle_info(self):
        vis = not self.metadata.isVisible()
        self.metadata.setVisible(vis)
        self.toggle_info_action.setIcon(
            panel_right_icon(20) if vis else panel_left_icon(20))
        self.toggle_info_action.setText("隐藏信息" if vis else "显示信息")

    def _on_about(self):
        QMessageBox.about(self, "关于 NCViewer",
                          "NCViewer\n\nNetCDF 查看与绘图桌面工具\n基于 PySide6 + xarray + matplotlib/cartopy")

    # ---------- 拖拽打开 ----------
    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """把拖入的 .nc/.nc4/.grb/.grib 文件逐个打开（多文件支持）。"""
        urls = event.mimeData().urls()
        opened = 0
        for url in urls:
            path = url.toLocalFile()
            if not path:
                continue
            low = path.lower()
            if low.endswith((".nc", ".nc4", ".cdf", ".grb", ".grib", ".grb2", ".grib2")):
                try:
                    self.open_file(path)
                    opened += 1
                except Exception as exc:
                    self.statusBar().showMessage(f"打开失败：{path}（{exc}）")
        if opened:
            self.statusBar().showMessage(f"已打开 {opened} 个数据集")
        event.acceptProposedAction()

    def closeEvent(self, event):
        self.settings.setValue("窗口位置", self.saveGeometry())
        self.settings.setValue("树列0宽度", self.tree.columnWidth(0))
        self.settings.setValue("树列1宽度", self.tree.columnWidth(1))
        super().closeEvent(event)

    def _refresh_actions(self):
        has = len(self.datasets) > 0
        self.remove_all_action.setEnabled(has)
        self.remove_one_action.setEnabled(has)
        self.create_plot_action.setEnabled(self._has_var_selected())
        # 合并绘图：≥2 个选中变量时可用
        n_var = sum(1 for it in self.tree.selectedItems()
                    if item_payload(it).get("kind") == "variable")
        self.combine_plot_action.setEnabled(n_var >= 2)

    def _has_var_selected(self) -> bool:
        item = self.tree.currentItem()
        return item is not None and item_payload(item).get("kind") == "variable"
