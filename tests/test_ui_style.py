"""NCViewer 样式和关键控件无头测试。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtWidgets import QApplication

from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style


def main():
    app = QApplication.instance() or QApplication([])
    apply_app_style(app)
    window = MainWindow()
    assert app.styleSheet().strip()
    assert window.tree is not None
    assert window.metadata is not None
    assert window.empty_state is not None
    window.open_file(r"D:\Agent\deepseek\ncviewer\data\demo_siconc.nc")
    plot = window.new_plot(window.datasets[0], "siconc")
    assert plot.slider is not None
    window.close()
    plot.close()
    print("UI 样式测试通过")


if __name__ == "__main__":
    main()
