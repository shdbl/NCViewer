"""NCViewer UI 无头冒烟测试（两级树：数据集 → 变量）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtWidgets import QApplication

from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.datatree import item_payload


def main():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    path = r"D:\Agent\deepseek\ncviewer\data\demo_siconc.nc"
    window.open_file(path)
    assert window.tree.topLevelItemCount() == 1
    root = window.tree.topLevelItem(0)
    # 两级树：数据集下直接是变量（无"变量"分组层）
    assert root.childCount() >= 1
    variable = root.child(0)
    payload = item_payload(variable)
    assert payload["kind"] == "variable"
    assert payload["var_name"] == "sic"
    window.tree.setCurrentItem(variable)
    assert window.metadata.stack.count() > 0
    plot = window.new_plot(payload["dataset"], payload["var_name"])
    assert plot.slider is not None
    before = plot.slider.value()
    plot.slider.setValue(1)
    assert plot.slider.value() != before
    # 数字输入联动：time_spin 改值 → slider 跟随
    assert plot.time_spin is not None
    plot.time_spin.setValue(5)
    assert plot.slider.value() == 4
    plot.canvas.draw()
    plot.close()
    window.close()
    print("UI 冒烟测试通过")


if __name__ == "__main__":
    main()
