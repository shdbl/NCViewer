"""数据树（Panoply 范式）：两级结构 数据集 → 变量，三列 名称|长名称|类型。

参照反编译的 NcDataTreeTableModel（Name|Long Name|Type 三列）实现。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from ncviewer.ui.icons import tree_icon

_USER_ROLE = int(Qt.ItemDataRole.UserRole)


def _var_type_text(var: dict, ds=None) -> str:
    """把变量的维度特征转成用户可读的类型文字（对齐 Panoply 的 Geo2D/1D 语义）。

    规则（尽量用科研语境的自然称呼）：
    - 带 2D 辅助经纬度坐标（curvilinear grid）→ 曲线网格经纬度场
    - 含经纬度维名且 ≥2 维 → 经纬度场（含时间则注明）
    - 一维时间 → 时间序列；一维其它 → 一维数组
    - 二维非经纬度 → 二维平面；三维 → 三维场；四维+ → N 维场
    """
    dims = var.get("dims", ())
    ndim = len(dims)
    low = [d.lower() for d in dims]
    has_lat = any(k in low for k in ("lat", "latitude"))
    has_lon = any(k in low for k in ("lon", "longitude"))
    # 时间类维度：time/valid_time（分析+预报），step 算 GRIB 预报的时间轴
    has_time = any(("time" in d) or (d in ("step", "valid_time")) for d in low)
    # 2D 辅助经纬度坐标（curvilinear grid）
    if ds is not None and ndim >= 2:
        from ncviewer.core.dataset import find_aux_lonlat
        try:
            if find_aux_lonlat(ds, var.get("name", "")) is not None:
                return "曲线网格经纬度场" + ("·含时间" if has_time else "")
        except Exception:
            pass
    if has_lat and has_lon and ndim >= 2:
        return "经纬度场" + ("·含时间" if has_time else "")
    if has_time and ndim == 1:
        return "时间序列"
    if ndim == 1:
        return "一维数组"
    if ndim == 2:
        return "二维平面"
    if ndim == 3:
        return "三维场"
    return f"{ndim}维场"


def build_tree(tree: QTreeWidget, ds, path: str, variables: list[dict],
               clear: bool = True) -> QTreeWidgetItem:
    """把数据集和变量构建成两级树。返回数据集根节点。

    ds: 打开的 xarray.Dataset；path: 原始文件路径；variables: describe_variables 的结果；
    clear: 追加打开数据集时传 False，避免清空先前已打开的数据集（多数据集并存）。
    """
    if clear:
        tree.clear()
    tree.setColumnCount(3)
    tree.setHeaderLabels(["名称", "长名称", "类型"])
    tree.setRootIsDecorated(True)
    tree.setUniformRowHeights(True)

    name = ds.attrs.get("title") or _stem(path)
    ds_item = QTreeWidgetItem(tree, [name, str(path), "数据集"])
    ds_item.setIcon(0, tree_icon("dataset", 16))
    ds_item.setData(0, _USER_ROLE, {"kind": "dataset", "path": str(path)})
    ds_item.setToolTip(1, str(path))

    for var in variables:
        var_name = var["name"]
        long_name = var.get("long_name") or ""
        vi = QTreeWidgetItem(ds_item, [var_name, str(long_name), _var_type_text(var, ds)])
        vi.setIcon(0, tree_icon("variable", 16))
        vi.setData(0, _USER_ROLE, {"kind": "variable", "dataset": str(path), "var_name": var_name})
        vi.setToolTip(0, var_name)
        if long_name:
            vi.setToolTip(1, str(long_name))
    ds_item.setExpanded(True)
    return ds_item


def _stem(path: str) -> str:
    """从文件路径取不带后缀的文件名。"""
    import os
    base = os.path.basename(str(path))
    low = base.lower()
    for suf in (".nc4", ".nc", ".grib2", ".grb2", ".grib", ".grb"):
        if low.endswith(suf):
            base = base[: -len(suf)]
            break
    return base


def item_payload(item: QTreeWidgetItem) -> dict:
    """取节点携带的数据载荷（kind=dataset|variable）。"""
    data = item.data(0, _USER_ROLE)
    return dict(data) if isinstance(data, dict) else {}
