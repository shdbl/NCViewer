"""S6.6 回归：多选/拖拽/类型文字/折叠组标题。"""
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Agent\deepseek")

from PySide6.QtWidgets import QApplication
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.datatree import _var_type_text
from ncviewer.ui.plot_controls import _make_collapsible

app = QApplication.instance() or QApplication([])

results = []

# 1) 类型文字自然化（y/x 是网格维，不算经纬度；含经纬度的多维 = 经纬度场）
cases = [
    ({"dims": ("time", "lat", "lon")}, "经纬度场·含时间"),
    ({"dims": ("time",)}, "时间序列"),
    ({"dims": ("x",)}, "一维数组"),
    ({"dims": ("y", "x")}, "二维平面"),
    ({"dims": ("time", "level", "lat", "lon")}, "经纬度场·含时间"),
    ({"dims": ("time", "level", "height", "lat", "lon")}, "经纬度场·含时间"),
    ({"dims": ("level", "y", "x")}, "三维场"),
]
ok = True
for var, expect in cases:
    got = _var_type_text(var)
    if got != expect:
        ok = False
        print(f"  ✗ {var['dims']}: got {got!r}, want {expect!r}")
results.append(("类型文字自然化", ok))

# 2) 折叠组标题可见（有非零高度 + 文本 + 箭头）
g, form = _make_collapsible("测试组")
g.show()
app.processEvents()
h = g._header
ok = h.text() == "测试组" and h.height() >= 20 and str(h.arrowType()) != "ArrowType.NoArrow"
results.append(("折叠组标题有高度", ok, f"h={h.height()} arrow={h.arrowType()}"))

# 3) 多选模式
w = MainWindow()
ok = "ExtendedSelection" in str(w.tree.selectionMode())
results.append(("树支持多选", ok, str(w.tree.selectionMode())))
ok = w.tree.acceptDrops() and w.acceptDrops()
results.append(("拖拽打开启用", ok))
w.close()

passed = sum(1 for r in results if r[1])
print(f"\n==== S6.6 回归: {passed}/{len(results)} 通过 ====")
for r in results:
    print(("[PASS] " if r[1] else "[FAIL] ") + r[0] + (f"  {r[2]}" if len(r) > 2 else ""))
sys.exit(0 if passed == len(results) else 1)
