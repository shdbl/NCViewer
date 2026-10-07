"""Plot Controls 面板集成与即时刷新闭环测试（无头）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PySide6.QtWidgets import QApplication, QDockWidget

from ncviewer.core.dataset import open_dataset
from ncviewer.ui.plot_window import PlotWindow


def main():
    app = QApplication.instance() or QApplication([])
    path = Path(__file__).resolve().parents[1] / "data" / "demo_siconc.nc"
    ds = open_dataset(str(path))

    window = PlotWindow(ds, "siconc")
    assert hasattr(window, "controls_panel"), "controls_panel 属性不存在"
    assert window.controls_panel is not None, "controls_panel 未创建"
    docks = window.findChildren(QDockWidget)
    assert len(docks) > 0, "未找到任何 QDockWidget"
    print("✓ Plot Controls dock 存在")

    controls = window.controls_panel
    controls.levels_spin.setValue(30)
    assert window.spec.levels == 30, f"等值线数量未同步：{window.spec.levels}"
    print("✓ C2 等值线数量同步")

    controls.projection_combo.setCurrentText("罗宾逊（Robinson）")
    assert window.spec.projection == "Robinson", f"投影未同步：{window.spec.projection}"
    try:
        window.refresh_plot()
        print("✓ C6 投影切换与重绘正常")
    except Exception as e:
        raise AssertionError(f"投影切换后重绘失败：{e}")

    controls.colormap_combo.setCurrentText("plasma")
    assert window.spec.colormap == "plasma", f"颜色表未同步：{window.spec.colormap}"
    print("✓ C8 颜色表切换同步")

    controls.title_edit.setText("测试标题")
    assert window.spec.title == "测试标题", f"标题未同步：{window.spec.title}"
    print("✓ C4 标题控件同步")

    controls.level_min_spin.setValue(0.0)
    controls.level_max_spin.setValue(100.0)
    assert window.spec.level_min == 0.0, f"最小值未同步：{window.spec.level_min}"
    assert window.spec.level_max == 100.0, f"最大值未同步：{window.spec.level_max}"
    print("✓ C2 最小值/最大值同步")

    controls.reset_button.click()
    assert window.spec.levels == 20 or window.spec.levels is None, f"重置后 levels 错误：{window.spec.levels}"
    assert window.spec.projection == "PlateCarree", f"重置后投影错误：{window.spec.projection}"
    print("✓ 重置按钮恢复默认")

    window.spec.plot_type = "line"
    controls.set_plot_type("line")
    assert not controls.projection_group.isEnabled(), "非地图类型时投影组应禁用"
    controls.set_plot_type("map")
    assert controls.projection_group.isEnabled(), "地图类型时投影组应启用"
    print("✓ 投影组启用/禁用逻辑正确")

    window.close()
    print("\n✓✓✓ Plot Controls 面板测试全部通过")


if __name__ == "__main__":
    main()
