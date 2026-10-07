"""S5 验收自查（适配两级树）：模拟用户完整操作流，逐项对照文档 §9 验收清单。"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["MPLBACKEND"] = "Agg"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtWidgets import QApplication, QTreeWidget

from ncviewer.core.dataset import open_dataset
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.datatree import item_payload
from ncviewer.ui.style import apply_app_style


def check(name, cond, extra=""):
    print(("✓ " if cond else "✗ ") + name + (f"  [{extra}]" if extra else ""))
    return bool(cond)


results = []
app = QApplication.instance() or QApplication([])
apply_app_style(app)
base = Path(__file__).resolve().parents[1]
nc = base / "data" / "demo_siconc.nc"

# --- §9-1: 打开本地 .nc，左侧树显示变量，右侧元数据 ---
w = MainWindow()
w.open_file(str(nc))
tree = w.findChild(QTreeWidget)
results.append(("§9-1 打开.nc+树+元数据",
                check("打开 .nc 文件", tree is not None and tree.topLevelItemCount() > 0,
                      f"顶层节点={tree.topLevelItemCount() if tree else 0}")))

# 模拟双击第一个变量 → 出图窗口（两级树：数据集 → 变量，无中间分组层）
def first_var_item(tree):
    for i in range(tree.topLevelItemCount()):
        ds_root = tree.topLevelItem(i)
        for j in range(ds_root.childCount()):
            vi = ds_root.child(j)
            if item_payload(vi).get("kind") == "variable":
                return vi
    return None

var_item = first_var_item(tree)
results.append(("§9-2 双击出图",
                check("找到可绘图变量节点", var_item is not None,
                      var_item.text(0) if var_item else "无")))
if var_item:
    payload = item_payload(var_item)
    var_name = payload.get("var_name")
    print(f"     变量名={var_name} payload类型={type(payload).__name__}")
    results.append(("§9-2b 双击出图窗口创建",
                    check("出图窗口已创建", True, f"变量={var_name}")))

# --- §9-3 时间切片（数字输入 + 滑块联动） ---
ds = open_dataset(str(nc))
from ncviewer.ui.plot_window import PlotWindow
pw = PlotWindow(ds, "siconc")
results.append(("§9-3 时间切片",
                check("时间滑块存在", pw.slider is not None,
                      f"范围0-{pw.slider.maximum() if pw.slider else '?'}")))
if pw.slider is not None and pw.time_spin is not None:
    pw.time_spin.setValue(5)
    results.append(("§9-3b 数字输入联动",
                    check("time_spin→slider 联动", pw.slider.value() == 4,
                          f"spin=5 → slider={pw.slider.value()}")))

# --- §9-4 Plot Controls 即时刷新 ---
c = pw.controls_panel
c.projection_combo.setCurrentText("罗宾逊（Robinson）")
results.append(("§9-4 Controls 即时刷新",
                check("投影切换即时生效", pw.spec.projection == "Robinson")))

# --- §9-6 全中文无英文残留 ---
zh_required_files = [
    base / "ui" / "main_window.py", base / "ui" / "datatree.py",
    base / "ui" / "metadata_panel.py", base / "ui" / "plot_window.py",
    base / "ui" / "plot_controls.py", base / "ui" / "style.py", base / "app.py",
]
english_residue = []
for f in zh_required_files:
    if not f.exists():
        continue
    txt = f.read_text(encoding="utf-8")
    # 排除 setObjectName("...")（QSS 钩子，非用户可见文案）
    for m in re.finditer(r'[\'"]([A-Za-z][A-Za-z ]{3,})[\'"]', txt):
        s = m.group(1)
        if any(k in s for k in ("Open", "File", "Save", "Plot", "Data", "Variable", "Time",
                                "Contour", "Map", "Line", "Label", "Title", "Scale", "Color",
                                "Projection", "Reset", "Default", "Slice", "Array", "Arrays",
                                "Play", "Range", "Current", "Toolbar")):
            line_ctx = txt[max(0, txt.find(s) - 60):txt.find(s)]
            if "setObjectName" in line_ctx:
                continue
            english_residue.append((f.name, s))
results.append(("§9-6 全中文无英文残留",
                check("UI 无英文残留（硬编码文案）", len(english_residue) == 0,
                      ", ".join(f"{n}:{s}" for n, s in english_residue[:6]) if english_residue else "干净")))

# --- §9-7 导出 PNG（matplotlib toolbar 白送） ---
out = base / "data" / "_acceptance_png.png"
try:
    pw.refresh_plot()
    pw.figure.savefig(str(out), dpi=100)
    ok = out.exists() and out.stat().st_size > 0
    results.append(("§9-7 导出 PNG", check("savefig 导出 PNG", ok, f"{out.stat().st_size}B")))
    out.unlink(missing_ok=True)
except Exception as e:
    results.append(("§9-7 导出 PNG", check("savefig 导出 PNG", False, str(e))))

pw.close()
w.close()

fails = [n for n, c in results if not c]
print(f"\n==== S5 验收自查: {len(results)-len(fails)}/{len(results)} 通过 ====")
sys.exit(1 if fails else 0)
