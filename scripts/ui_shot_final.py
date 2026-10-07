"""渲染最终版 UI 截图（主窗口 + 绘图窗口），注册 Windows 字体解决无头豆腐块。"""
from __future__ import annotations
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Agent\deepseek")

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style

app = QApplication([])
_fd = QFontDatabase()
for _f in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
           r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttf"):
    try:
        _fd.addApplicationFont(_f)
    except Exception:
        pass
apply_app_style(app)

w = MainWindow()
w.open_file(r"D:\Agent\deepseek\ncviewer\data\demo_siconc.nc")
w.resize(1200, 760)
w.show()
app.processEvents()
# 选中第一个变量显示概览 + 原始信息
tree = w.tree
vi = tree.topLevelItem(0).child(0)
tree.setCurrentItem(vi)
app.processEvents()
w.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_main.png")
print("主窗口截图 OK")

# 切到原始信息标签页再截一张
app.processEvents()
w.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_raw.png")
print("原始信息页截图 OK")

pw = w.new_plot(w.datasets[0], "siconc")
pw.resize(1100, 720)
pw.show()
pw.time_spin.setValue(5)
pw.refresh_plot()
app.processEvents()
pw.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_plot.png")
print("绘图窗口截图 OK")
pw.tabs.setCurrentIndex(1)
app.processEvents()
pw.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_data.png")
print("数据视图截图 OK")
pw.tabs.setCurrentIndex(2)
app.processEvents()
pw.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_meta.png")
print("元数据视图截图 OK")

# 新控件效果：log scale + normalize + 等值线样式 + minmax 标注
pw.tabs.setCurrentIndex(0)
pw.spec.log_scale = False
pw.spec.normalize = True
pw.spec.contour_style = "both"
pw.spec.show_minmax = True
pw.spec.contour_labels = True
pw.refresh_plot()
app.processEvents()
pw.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_options.png")
print("新选项效果截图 OK")

# 合成图
from ncviewer.ui.plot_window import CombinePlotWindow
cp = CombinePlotWindow([(w.datasets[0], "siconc")])
cp.resize(1000, 680)
cp.show()
app.processEvents()
cp.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_final_combine.png")
print("合成图截图 OK")

w.close()
pw.close()
cp.close()
