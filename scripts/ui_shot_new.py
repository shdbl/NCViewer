"""无头渲染 NCViewer 实际界面并保存截图用于设计复验。

生成文件：
- data/_ui_new_main.png (主窗口)
- data/_ui_new_plot.png (绘图窗口及 Plot Controls dock)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QSize
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style


def main() -> None:
    app = QApplication.instance() or QApplication([])

    for font_file in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ):
        if os.path.exists(font_file):
            QFontDatabase.addApplicationFont(font_file)

    apply_app_style(app)

    data_dir = project_root / "ncviewer" / "data"
    nc_path = data_dir / "demo_siconc.nc"

    window = MainWindow()
    if nc_path.exists():
        window.open_file(str(nc_path))
        # 选中第一个变量，让右侧元数据面板展示变量信息
        tree = window.tree
        if tree.topLevelItemCount():
            ds_root = tree.topLevelItem(0)
            if ds_root.childCount():
                grp = ds_root.child(0)
                if grp.childCount():
                    tree.setCurrentItem(grp.child(0))
                    window._selection_changed()
    window.resize(QSize(1100, 720))
    window.show()
    app.processEvents()

    main_shot_path = data_dir / "_ui_new_main.png"
    window.grab().save(str(main_shot_path), "PNG")
    print(f"主窗口截图保存至: {main_shot_path} ({main_shot_path.stat().st_size} 字节)")

    plot_shot_path = data_dir / "_ui_new_plot.png"
    if window.datasets:
        plot = window.new_plot(window.datasets[0], "siconc")
        plot.resize(QSize(1180, 800))
        plot.show()
        app.processEvents()
        if hasattr(plot, "refresh_plot"):
            plot.refresh_plot()
            app.processEvents()
        plot.grab().save(str(plot_shot_path), "PNG")
        print(f"绘图窗口截图保存至: {plot_shot_path} ({plot_shot_path.stat().st_size} 字节)")
        plot.close()

    window.close()


if __name__ == "__main__":
    main()
