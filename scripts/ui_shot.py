"""S5.5 深色主题视觉自审：渲染主窗口 + 绘图窗口截图。"""
from __future__ import annotations
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Agent\deepseek")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style

app = QApplication([])
# offscreen 无头环境注册 Windows 字体，避免中文渲染成豆腐块
_fd = QFontDatabase()
for _f in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
           r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttf"):
    try:
        _fd.addApplicationFont(_f)
    except Exception:
        pass
apply_app_style(app)

# 主窗口 + 打开演示数据 + 选中变量
w = MainWindow()
w.open_file(r"D:\Agent\deepseek\ncviewer\data\demo_siconc.nc")
w.resize(1200, 760)
w.show()
app.processEvents()

# 选中第一个变量显示元数据
from ncviewer.ui.datatree import item_payload
tree = w.tree
ds_root = tree.topLevelItem(0)
grp = ds_root.child(0)
vi = grp.child(0)
tree.setCurrentItem(vi)
app.processEvents()
w.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_main_dark.png")
print("主窗口截图:", w.grab().size().width(), "x", w.grab().size().height())

# 绘图窗口
pw = w.new_plot(w.datasets[0], "siconc")
pw.resize(1000, 700)
pw.show()
pw.refresh_plot()
app.processEvents()
pw.grab().save(r"D:\Agent\deepseek\ncviewer\data\_ui_plot_dark.png")
print("绘图窗口截图:", pw.grab().size().width(), "x", pw.grab().size().height())
w.close()
pw.close()
