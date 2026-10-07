"""NCViewer 图标：Panoply 官方 PNG 图标（从 Panoply.jar 提取）+ 现代线性 SVG 图标兜底。

官方图标（ui/resources/*.png，144x144 源图缩放为 36px 工具栏图标 / 64x64 树图标缩放 16px）。
"""
from __future__ import annotations

import os

from PySide6.QtCore import QByteArray, Qt, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

_RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

# ---- Panoply 官方图标（从 Panoply.jar 提取） ----
_PANOPLY_ICONS = {
    "create_plot": "createplot_144x144.png",
    "combine_plot": "combineplot_144x144.png",
    "open_dataset": "opendataset_144x144.png",
    "remove_one": "removeone_144x144.png",
    "remove_all": "removeall_144x144.png",
    "hide_info": "hideinfo_144x144.png",
    "show_info": "showinfo_144x144.png",
    "folder": "ttfolder_64x64.png",
    "leaf": "ttleaf_64x64.png",
}


def panoply_icon(name: str, size: int = 36) -> QIcon:
    """加载 Panoply 官方 PNG 图标并缩放到指定尺寸（高清下提供 2x）。"""
    fname = _PANOPLY_ICONS.get(name)
    if not fname:
        return QIcon()
    path = os.path.join(_RES_DIR, fname)
    if not os.path.exists(path):
        return QIcon()
    icon = QIcon(path)
    if size > 0:
        pm = QPixmap(path).scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(pm)
    return icon


# ---- 线性 SVG 图标（stroke 风格，兜底/细节图标） ----

_FOLDER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>"""

_FILE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>"""

_OPEN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><path d="M2 12h20"/></svg>"""

_REFRESH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 21v-5h5"/></svg>"""

_PLAY = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3" fill="{stroke}" stroke="none"/></svg>"""

_STEP_LEFT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="15.5,17.5 8.5,12 15.5,6.5" fill="{stroke}"/></svg>"""

_STEP_RIGHT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><polygon points="8.5,17.5 15.5,12 8.5,6.5" fill="{stroke}"/></svg>"""

_DATASET = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/></svg>"""

# ---- 工具栏线性图标（现代 Feather 风格，替代拟物位图） ----
_CHART = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>"""

_LAYERS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>"""

_TRASH = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>"""

_TRASH2 = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>"""

_PANEL_RIGHT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="15" y1="3" x2="15" y2="21"/></svg>"""

_PANEL_LEFT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>"""


def _svg_icon(svg_body: str, size: int = 16, stroke: str = "#4a5568") -> QIcon:
    """把 SVG 字符串渲染为指定尺寸的 QIcon（高 DPI 下仍清晰）。"""
    svg = svg_body.format(stroke=stroke)
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pm)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    icon = QIcon(pm)
    pm2 = QPixmap(size * 2, size * 2)
    pm2.fill(Qt.GlobalColor.transparent)
    renderer2 = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    p2 = QPainter(pm2)
    renderer2.render(p2, QRectF(0, 0, size * 2, size * 2))
    p2.end()
    icon.addPixmap(pm2)
    return icon


def folder_icon(size: int = 16) -> QIcon:
    return _svg_icon(_FOLDER, size)


def file_icon(size: int = 16) -> QIcon:
    return _svg_icon(_FILE, size)


def open_icon(size: int = 18) -> QIcon:
    return _svg_icon(_OPEN, size)


def refresh_icon(size: int = 18) -> QIcon:
    return _svg_icon(_REFRESH, size)


def play_icon(size: int = 16) -> QIcon:
    return _svg_icon(_PLAY, size)


def step_left_icon(size: int = 14) -> QIcon:
    return _svg_icon(_STEP_LEFT, size, stroke="#3b4a5a")


def step_right_icon(size: int = 14) -> QIcon:
    return _svg_icon(_STEP_RIGHT, size, stroke="#3b4a5a")


def dataset_icon(size: int = 16) -> QIcon:
    return _svg_icon(_DATASET, size)


def chart_icon(size: int = 20) -> QIcon:
    """创建绘图（柱状图符号）。"""
    return _svg_icon(_CHART, size, stroke="#316dc3")


def layers_icon(size: int = 20) -> QIcon:
    """合并绘图（多层叠加符号，与单图明确区分）。"""
    return _svg_icon(_LAYERS, size, stroke="#316dc3")


def trash_icon(size: int = 20) -> QIcon:
    """移除一个（垃圾桶）。"""
    return _svg_icon(_TRASH, size, stroke="#4a5568")


def trash_all_icon(size: int = 20) -> QIcon:
    """移除全部（垃圾桶带内容）。"""
    return _svg_icon(_TRASH2, size, stroke="#4a5568")


def panel_right_icon(size: int = 20) -> QIcon:
    """隐藏信息（右侧面板切换）。"""
    return _svg_icon(_PANEL_RIGHT, size, stroke="#4a5568")


def panel_left_icon(size: int = 20) -> QIcon:
    """显示信息（左侧面板切换）。"""
    return _svg_icon(_PANEL_LEFT, size, stroke="#4a5568")


def app_icon(size: int = 64) -> QIcon:
    """应用图标（AI 生成的高端地球气象图标，PNG/ICO）。

    源码运行时从 ui/resources 加载；打包后从 _MEIPASS 解析。
    """
    import sys as _sys
    res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
        res_dir = os.path.join(_sys._MEIPASS, "ncviewer", "ui", "resources")
    png = os.path.join(res_dir, "ncviewer_icon.png")
    if os.path.exists(png):
        pm = QPixmap(png)
        if size > 0:
            pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        return QIcon(pm)
    return QIcon()
