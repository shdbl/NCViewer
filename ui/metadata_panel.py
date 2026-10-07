"""元数据面板（Panoply 范式）：「概览 / 原始信息」两个标签页。

- 概览：选中变量时显示 变量信息 + 时间维度块 + 空间维度块（坐标值首尾预览）；
        选中数据集时显示 数据集信息 + 全局属性。
- 原始信息：CDL 语法（netcdf file {...}）等宽全文，英文原名、dtype/dims/shape/attrs/encoding。
"""
from __future__ import annotations

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QHeaderView, QHBoxLayout, QLabel, QScrollArea,
    QSplitter, QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from ncviewer.core.dataset import describe_global_attrs, describe_variables, get_time_info


class _CDLHighlighter(QSyntaxHighlighter):
    """netcdf CDL 语法高亮（Panoply View Metadata 同款：关键字/类型/属性/注释分色）。"""

    def __init__(self, document):
        super().__init__(document)
        fmt_key = QTextCharFormat()
        fmt_key.setForeground(QColor("#316dc3"))
        fmt_key.setFontWeight(QFont.Weight.Bold)
        fmt_type = QTextCharFormat()
        fmt_type.setForeground(QColor("#8250df"))
        fmt_attr = QTextCharFormat()
        fmt_attr.setForeground(QColor("#57606a"))
        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#8c959f"))
        fmt_comment.setFontItalic(True)
        self._rules = [
            (QRegularExpression(r"^\s*(dimensions|variables|// global attributes):"), fmt_key),
            (QRegularExpression(r"\b(int|float|double|short|byte|char|string|int64|uint)\b"),
             fmt_type),
            (QRegularExpression(r"^\s*:\w+"), fmt_attr),
            (QRegularExpression(r"//.*$"), fmt_comment),
        ]

    def highlightBlock(self, text):
        for regex, fmt in self._rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


def _fmt_value(value, limit: int = 80) -> str:
    """把元数据值格式化为可读文本，超长截断。"""
    text = str(value)
    return text if len(text) <= limit else text[: limit - 3] + "…"


def _preview(coord_values, limit: int = 4) -> str:
    """坐标值预览：首尾各 limit 个，中间用省略号，对齐 xarray 控制台预览。"""
    n = len(coord_values)
    if n <= 2 * limit:
        return ", ".join(_fmt_value(v, 24) for v in coord_values)
    head = ", ".join(_fmt_value(v, 24) for v in coord_values[:limit])
    tail = ", ".join(_fmt_value(v, 24) for v in coord_values[-limit:])
    return f"{head}, …, {tail}"


def cdl_text(ds, var_name: str | None = None) -> str:
    """生成 netcdf CDL 语法文本（Panoply 式全元数据）。

    var_name=None 时为数据集级 CDL；否则仅该变量（含维度与全局属性）。
    """
    lines = []
    lines.append("netcdf file {")
    lines.append("dimensions:")
    dims = ds.sizes
    for dname, dlen in dims.items():
        lines.append(f"\t{dname} = {dlen} ;")
    lines.append("variables:")
    if var_name is not None:
        names = [var_name]
    else:
        names = [n for n in ds.variables if n not in ds.coords]
        names += [n for n in ds.coords]
    for name in names:
        da = ds[name]
        dim_str = "(" + ", ".join(da.dims) + ")" if da.dims else ""
        lines.append(f"\t{da.dtype} {name}{dim_str} ;")
        for k, v in da.attrs.items():
            lines.append(f"\t\t{name}:{k} = {v!r} ;")
    lines.append("// global attributes:")
    for k, v in ds.attrs.items():
        lines.append(f"\t\t:{k} = {v!r} ;")
    lines.append("}")
    return "\n".join(lines)


def cdl_html(ds, var_name: str | None = None) -> str:
    """结构化 HTML 元数据：变量名作块标题（accent 底色），键值行、全局属性区。

    用于「查看元数据」视图，比纯文本 CDL 易读（Panoply View Metadata 人性化版）。
    """
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    parts = ['<div style="font-family:Consolas,Menlo,monospace;font-size:9pt;'
             'color:#24292f;line-height:1.7;">']

    def var_block(name, da):
        block = ['<div style="margin:2px 0 8px 0;">']
        block.append(
            f'<div style="background:#e3f0fc;color:#1f4d8f;font-weight:bold;'
            f'font-size:10pt;padding:4px 10px;border-radius:4px;margin-bottom:6px;">'
            f'{esc(name)}</div>')
        rows = [("类型", str(da.dtype)),
                ("维度", ", ".join(da.dims) if da.dims else "无"),
                ("形状", "(" + ", ".join(f"{d}:{n}" for d, n in zip(da.dims, da.shape)) + ")")]
        if da.attrs.get("units"):
            rows.append(("单位", str(da.attrs["units"])))
        if da.attrs.get("long_name"):
            rows.append(("长名称", str(da.attrs["long_name"])))
        for k, v in da.attrs.items():
            if k in ("units", "long_name"):
                continue
            rows.append((str(k), _fmt_value(v, 140)))
        for k, v in rows:
            block.append(
                f'<div style="padding:1px 4px;"><span style="color:#57606a;'
                f'display:inline-block;min-width:70px;">{esc(k)}</span>'
                f'<span>{esc(v)}</span></div>')
        block.append("</div>")
        return "".join(block)

    if var_name is not None:
        names = [var_name]
    else:
        names = [n for n in ds.variables if n not in ds.coords] + [n for n in ds.coords]
    for name in names:
        parts.append(var_block(name, ds[name]))

    if ds.attrs:
        g = ['<div style="background:#f3f5f8;color:#24292f;font-weight:bold;'
             'font-size:10pt;padding:4px 10px;border-radius:4px;margin:10px 0 6px 0;">'
             '全局属性</div>']
        for k, v in ds.attrs.items():
            if k == "_ncviewer_source_path":
                continue
            g.append(f'<div style="padding:1px 4px;"><span style="color:#57606a;">'
                     f'{esc(k)}</span>&nbsp;&nbsp;<span>{esc(_fmt_value(v, 140))}</span></div>')
        parts.append("".join(g))
    parts.append("</div>")
    return "".join(parts)


class _SectionCard(QFrame):
    """PyCharm 式分区卡片：标题 + 表单。"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metaSection")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(4)
        self.title = QLabel(title)
        self.title.setObjectName("sectionTitle")
        lay.addWidget(self.title)
        self.form_host = QWidget()
        self.form = QFormLayout(self.form_host)
        self.form.setContentsMargins(0, 2, 0, 0)
        self.form.setHorizontalSpacing(16)
        self.form.setVerticalSpacing(5)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self.form_host)


class MetadataPanel(QWidget):
    """主窗口右侧元数据面板：概览 / 原始信息 两个标签页。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = None  # 旧接口兼容
        self._ds = None
        self._current_var = None
        self._cards: dict[str, _SectionCard] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        # --- 概览页（内部用 stack 承载，向上兼容 stack.count()>0） ---
        self.overview = QScrollArea()
        self.overview.setWidgetResizable(True)
        self.overview.setFrameShape(QFrame.Shape.NoFrame)
        self.overview_stack = QStackedWidget()
        self.stack = self.overview_stack
        self.overview.setWidget(self.overview_stack)

        self._overview_page = QWidget()
        self._ov_layout = QVBoxLayout(self._overview_page)
        self._ov_layout.setContentsMargins(4, 4, 4, 4)
        self._ov_layout.setSpacing(8)
        self.overview_stack.addWidget(self._overview_page)

        self.tabs.addTab(self.overview, "概览")

        # --- 原始信息页（CDL 等宽全文 + 语法高亮） ---
        self.raw_info = QTextEdit()
        self.raw_info.setObjectName("rawInfo")
        self.raw_info.setReadOnly(True)
        self.raw_info.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._cdl_hl = _CDLHighlighter(self.raw_info.document())
        self.tabs.addTab(self.raw_info, "原始信息")

    # ---------- 对外接口 ----------
    def set_dataset(self, ds) -> None:
        """打开新数据集时重置面板。"""
        self._ds = ds
        self._current_var = None
        self.clear_panel()
        self.show_item(ds)

    def show_item(self, ds, var_name: str | None = None) -> None:
        """显示数据集或变量信息。var_name=None 显示数据集级信息。"""
        self._ds = ds
        self._current_var = var_name
        self.clear_panel()
        if ds is None:
            return
        if var_name is None:
            self._add_dataset_card(ds)
        else:
            self._add_variable_card(ds, var_name)
        self.raw_info.setPlainText(cdl_text(ds, var_name))
        self.overview_stack.setCurrentIndex(0)

    def clear_panel(self) -> None:
        """清空概览页卡片，保留布局结构（stretch 由 _SectionCard 内部承担）。"""
        while self._ov_layout.count():
            item = self._ov_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._cards.clear()

    # ---------- 卡片构建 ----------
    def _add_card(self, title: str) -> _SectionCard:
        card = _SectionCard(title)
        self._ov_layout.addWidget(card)
        self._cards[title] = card
        return card

    def _add_pair(self, card: _SectionCard, key: str, value) -> None:
        k = QLabel(key)
        k.setObjectName("metaKey")
        v = QLabel(_fmt_value(value))
        v.setObjectName("metaValue")
        v.setWordWrap(True)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card.form.addRow(k, v)

    def _add_variable_card(self, ds, var_name: str) -> None:
        """变量信息：PyCharm Variables 式表格（属性 | 值），等宽对齐。"""
        da = ds[var_name]
        card = self._add_card("变量信息")

        table = QTableWidget()
        table.setObjectName("metaTable")
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["属性", "值"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)

        shape_txt = "(" + ", ".join(f"{d}:{n}" for d, n in zip(da.dims, da.shape)) + ")"
        rows = [("变量名", var_name),
                ("类型", str(da.dtype)),
                ("形状", shape_txt)]
        if da.attrs.get("units"):
            rows.append(("单位", str(da.attrs["units"])))
        if da.attrs.get("long_name"):
            rows.append(("长名称", str(da.attrs["long_name"])))
        for k, v in da.attrs.items():
            if k in ("units", "long_name"):
                continue
            rows.append((k, _fmt_value(v, 120)))
        table.setRowCount(len(rows))
        for i, (k, v) in enumerate(rows):
            ki = QTableWidgetItem(k)
            ki.setForeground(QColor("#57606a"))  # 属性键（比正文略灰但清晰）
            vi = QTableWidgetItem(v)
            vi.setToolTip(v)
            table.setItem(i, 0, ki)
            table.setItem(i, 1, vi)
        card.layout().addWidget(table)

        # 维度信息（表格形式）——与变量信息一起放进可调垂直分割器（默认 6:4）
        dim_card = self._make_dimension_card(ds, da)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.addWidget(card)
        splitter.addWidget(dim_card)
        splitter.setSizes([220, 145])  # 6:4 默认比例，用户可拖动分隔条
        self._ov_layout.addWidget(splitter)
        self._cards["变量信息"] = card
        self._cards["维度信息"] = dim_card

    def _make_dimension_card(self, ds, da) -> _SectionCard:
        """维度信息：PyCharm 式表格（维度 | 大小 | 坐标预览），时间维高亮。

        返回卡片（由调用方挂进垂直分割器，与变量信息 6:4 可调）。
        """
        card = _SectionCard("维度信息")
        time_info = None
        try:
            time_info = get_time_info(ds, da.name)
        except Exception:
            pass

        table = QTableWidget()
        table.setObjectName("metaTable")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["维度", "大小", "坐标 / 预览"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)

        rows = []
        for d in da.dims:
            is_time = time_info is not None and time_info["dim"] == d
            if d in ds.coords:
                vals = ds[d].values
                preview = _preview(vals)
                if is_time and time_info is not None:
                    preview = f"{time_info['start']} … {time_info['end']}"
            else:
                preview = "（无坐标）"
            rows.append((d, str(ds.sizes[d]), preview, is_time))

        table.setRowCount(len(rows))
        for i, (d, size, preview, is_time) in enumerate(rows):
            di = QTableWidgetItem(d)
            si = QTableWidgetItem(size)
            pi = QTableWidgetItem(preview)
            pi.setToolTip(preview)
            if is_time:
                for it in (di, si, pi):
                    it.setBackground(QColor("#e3f0fc"))
                    it.setForeground(QColor("#316dc3"))
            table.setItem(i, 0, di)
            table.setItem(i, 1, si)
            table.setItem(i, 2, pi)
        card.layout().addWidget(table)
        return card

    def _add_dataset_card(self, ds) -> None:
        card = _SectionCard("数据集信息")
        self._add_pair(card, "名称", ds.attrs.get("title") or "（无标题）")
        src = ds.attrs.get("_ncviewer_source_path")
        if src:
            self._add_pair(card, "路径", src)
        self._add_pair(card, "变量数", len(describe_variables(ds)))

        # 变量总览表（Panoply 选中数据集时显示的变量列表摘要）
        varcard = _SectionCard("变量列表")
        table = QTableWidget()
        table.setObjectName("metaTable")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["名称", "类型", "形状"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        rows = []
        for n in ds.data_vars:
            da = ds[n]
            shape = "(" + ", ".join(f"{d}:{s}" for d, s in zip(da.dims, da.shape)) + ")"
            rows.append((n, str(da.dtype), shape))
        for n in ds.coords:
            da = ds[n]
            shape = "(" + ", ".join(f"{d}:{s}" for d, s in zip(da.dims, da.shape)) + ")"
            rows.append((n, str(da.dtype), shape))
        table.setRowCount(len(rows))
        for i, (n, t, s) in enumerate(rows):
            ni = QTableWidgetItem(n)
            ni.setForeground(QColor("#316dc3"))
            ti = QTableWidgetItem(t)
            si = QTableWidgetItem(s)
            si.setToolTip(s)
            table.setItem(i, 0, ni)
            table.setItem(i, 1, ti)
            table.setItem(i, 2, si)
        varcard.layout().addWidget(table)

        g = describe_global_attrs(ds)
        gcard = None
        if g:
            gcard = _SectionCard("全局属性")
            for k, v in g.items():
                self._add_pair(gcard, k, v)

        # 三个卡片放进可调垂直分割器（默认按内容比例分配）
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.addWidget(card)
        splitter.addWidget(varcard)
        if gcard is not None:
            splitter.addWidget(gcard)
        # 默认比例：数据集信息 ≈ 1 行、变量列表按行数、全局属性按条目数
        n_var = max(1, len(ds.data_vars) + len(ds.coords))
        n_g = max(1, len(g)) if g else 0
        splitter.setSizes([90, max(120, n_var * 26), max(80, n_g * 26)])
        self._ov_layout.addWidget(splitter)
        self._cards["数据集信息"] = card
        self._cards["变量列表"] = varcard
        if gcard is not None:
            self._cards["全局属性"] = gcard
