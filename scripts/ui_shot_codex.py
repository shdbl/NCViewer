# -*- coding: utf-8 -*-
"""生成 NCViewer 主题验收截图（无头 Qt）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style


def register_fonts() -> None:
    """注册 Windows 中文字体，避免离屏渲染出现方块。"""
    for path in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if Path(path).exists():
            QFontDatabase.addApplicationFont(path)


def first_variable(window):
    """按契约取数据集→变量组→变量的第一个变量节点。"""
    root = window.tree.topLevelItem(0)
    if root is None or root.childCount() == 0:
        return None
    group = root.child(0)
    return group.child(0) if group.childCount() else None


app = QApplication.instance() or QApplication(sys.argv)
register_fonts()
apply_app_style(app)

out_dir = ROOT / "data"
out_dir.mkdir(parents=True, exist_ok=True)
nc_path = out_dir / "demo_siconc.nc"

window = MainWindow()
window.setWindowTitle("NCViewer · 纸白科研工作台")
window.resize(1440, 900)
window.open_file(str(nc_path))
item = first_variable(window)
if item is not None:
    window.tree.setCurrentItem(item)
    window.tree.scrollToItem(item)
app.processEvents()
window.grab().save(str(out_dir / "_ui_codex_main.png"))

plot = None
try:
    if item is not None:
        payload = item.data(0, 32)
        # 主窗口已有 new_plot 契约；优先通过当前节点创建，确保元数据与图联动。
        plot = window.new_plot(window.datasets[0], "siconc")
    else:
        plot = window.new_plot(window.datasets[0], "siconc")
    plot.setWindowTitle("NCViewer · 图形页")
    plot.resize(1280, 820)
    plot.show()
    app.processEvents()
    plot.grab().save(str(out_dir / "_ui_codex_plot.png"))
finally:
    if plot is not None:
        plot.close()
    window.close()
    app.processEvents()

print(out_dir / "_ui_codex_main.png")
print(out_dir / "_ui_codex_plot.png")
