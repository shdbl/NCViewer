"""NCViewer 全局 Qt 样式 —— PyCharm/幕布式浅色专业主题（S6 质感精修版）。

设计语言（用户指定参考 PyCharm / 幕布）：
- IntelliJ Light 血统：浅灰蓝窗口 + 白面板 + 细边框 + JetBrains 蓝 accent
- 小圆角（6px）统一、细分割线；高信息密度但留白舒适
- 全控件定制（滚动条/下拉/单选/复选/滑块/菜单/提示框），消灭系统默认
- 对比度：正文 #24292f on #ffffff ≈ 14:1；次要 #57606a ≈ 7:1；弱提示 #8c959f ≈ 4.6:1

S6 质感精修（本版）：
- 统一控件高度 30px（按钮/输入/下拉/树项），可点击区域舒适
- 按钮从"白底链接感"改为 PyCharm 式浅灰实底 + 边框，hover/pressed 逐级加深模拟按压缩放
- 全局字体加 letter-spacing 0.5px，中文更舒展；标题/正文/辅助三级字号
- 间距系统化：输入 3px 10px、按钮 6px 18px、树项 4px 8px、菜单 8px 30px 8px 14px
- 树选中项左侧 3px accent 竖条（PyCharm 风格选中指示）
"""
from __future__ import annotations

import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

# 箭头图标资源（ui/resources/arrow_*.png），QSS url 需绝对路径
_RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
_ARROW_DOWN = os.path.join(_RES_DIR, "arrow_down.png").replace("\\", "/")
_ARROW_UP = os.path.join(_RES_DIR, "arrow_up.png").replace("\\", "/")
_ARROW_RIGHT = os.path.join(_RES_DIR, "arrow_right.png").replace("\\", "/")

# ---- 设计令牌 ----
BG_WINDOW = "#e9edf3"      # 窗口背景（浅灰蓝，略深于面板形成层次）
BG_PANEL = "#ffffff"       # 面板/树/滚动区（白）
BG_RAISED = "#f3f5f8"      # 输入框/浮层/工具栏
BG_HOVER = "#e7ecf3"       # hover 态
BG_ACTIVE = "#cfe3f7"      # 选中/激活态（浅蓝）
ACCENT = "#316dc3"         # JetBrains 蓝（主强调）
ACCENT_LIGHT = "#4a86d6"   # 强调亮色
ACCENT_BG = "#e3f0fc"      # 强调浅底
BORDER = "#d8dee6"         # 常规边框
BORDER_LIGHT = "#bcc8d4"   # 输入框/悬停边框
TEXT = "#24292f"           # 正文（近黑）
TEXT_DIM = "#57606a"       # 次要文字
TEXT_FAINT = "#8c959f"     # 弱提示
ON_ACCENT = "#ffffff"      # 强调背景上的文字

# ---- 尺寸令牌 ----
CTRL_H = 30                # 控件基准高度（px）
RADIUS = 6                 # 统一圆角


def apply_app_style(app: QApplication) -> None:
    """设置统一字体（含轻微字距）、色彩、间距、焦点和控件状态。"""
    font = QFont("Microsoft YaHei", 10)
    font.setStyleHint(QFont.SansSerif)
    font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)  # 全局字距，中文更舒展
    app.setFont(font)
    app.setStyleSheet(_QSS)


_QSS = f"""
/* ============ 基础 ============ */
QWidget {{
    color: {TEXT};
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    font-size: 10pt;
    selection-background-color: {ACCENT};
    selection-color: {ON_ACCENT};
}}
QLabel {{
    background: transparent;
}}
QMainWindow, QDialog {{
    background: {BG_WINDOW};
}}
QWidget:disabled {{
    color: {TEXT_FAINT};
}}
QScrollArea {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}
QScrollArea > QWidget > QWidget {{
    background: {BG_PANEL};
}}

/* ============ 菜单 ============ */
QMenuBar {{
    background: {BG_WINDOW};
    border-bottom: 1px solid {BORDER};
    padding: 3px 10px;
}}
QMenuBar::item {{
    padding: 7px 14px;
    border-radius: {RADIUS}px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background: {BG_HOVER};
}}
QMenuBar::item:pressed {{
    background: {BG_ACTIVE};
}}
QMenu {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 30px 8px 14px;
    border-radius: {RADIUS}px;
    background: transparent;
}}
QMenu::item:selected {{
    background: {ACCENT_BG};
    color: {TEXT};
}}
QMenu::item:disabled {{
    color: {TEXT_FAINT};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 6px 10px;
}}

/* ============ 工具栏 ============ */
QToolBar {{
    background: {BG_PANEL};
    border: 0;
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
    padding: 6px 10px;
}}
QToolBar::separator {{
    width: 1px;
    background: {BORDER};
    margin: 5px 10px;
}}
QToolButton {{
    min-height: {CTRL_H}px;
    padding: 4px 10px;
    border-radius: {RADIUS}px;
    background: transparent;
    color: {TEXT};
    border: 1px solid transparent;
}}
QToolButton:hover {{
    background: {BG_HOVER};
    border: 1px solid {BORDER_LIGHT};
}}
QToolButton:pressed {{
    background: {BG_ACTIVE};
}}
QToolButton:checked {{
    background: {ACCENT_BG};
    color: {ACCENT};
}}

/* ============ 按钮（PyCharm 式浅灰实底） ============ */
QPushButton {{
    min-height: {CTRL_H}px;
    padding: 4px 18px;
    border-radius: {RADIUS}px;
    background: {BG_RAISED};
    border: 1px solid {BORDER_LIGHT};
    color: {TEXT};
    font-weight: 500;
}}
QPushButton:hover {{
    background: {BG_HOVER};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background: {BG_ACTIVE};
    border-color: {ACCENT};
}}
QPushButton:default {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: {ON_ACCENT};
    font-weight: 600;
}}
QPushButton:default:hover {{
    background: {ACCENT_LIGHT};
}}
QPushButton:disabled {{
    background: {BG_RAISED};
    border-color: {BORDER};
    color: {TEXT_FAINT};
}}

/* ============ 树（PyCharm 式选中竖条） ============ */
QTreeWidget {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 4px;
    outline: 0;
}}
QTreeWidget::item {{
    min-height: {CTRL_H}px;
    padding: 4px 8px;
    border-radius: 4px;
    color: {TEXT};
}}
QTreeWidget::item:hover {{
    background: {BG_HOVER};
}}
QTreeWidget::item:selected {{
    background: {ACCENT_BG};
    color: {ACCENT};
    font-weight: 500;
    border: 0;
    border-radius: 4px;
}}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    image: url("{_ARROW_RIGHT}");
    width: 10px;
    height: 6px;
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    image: url("{_ARROW_DOWN}");
    width: 10px;
    height: 6px;
}}
QHeaderView::section {{
    background: {BG_RAISED};
    color: {TEXT_DIM};
    font-weight: 600;
    padding: 8px 10px;
    border: 0;
    border-bottom: 1px solid {BORDER};
}}

/* ---- 元数据表格（PyCharm Variables 网格） ---- */
QTableWidget#metaTable {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    gridline-color: {BORDER};
    font-size: 9.5pt;
    selection-background-color: {ACCENT_BG};
    selection-color: {TEXT};
}}
QTableWidget#metaTable::item {{
    padding: 4px 8px;
    border: 0;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget#metaTable::item:selected {{
    background: {ACCENT_BG};
    color: {TEXT};
}}
QTableWidget#metaTable QTableCornerButton::section {{
    background: {BG_RAISED};
    border: 0;
}}
QTableWidget#metaTable QHeaderView::section {{
    background: {BG_RAISED};
    color: {TEXT_DIM};
    font-weight: 600;
    font-size: 9pt;
    padding: 6px 8px;
    border: 0;
    border-bottom: 1px solid {BORDER};
}}

/* ============ 标签页 ============ */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    background: {BG_PANEL};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_DIM};
    padding: 9px 18px;
    border: 0;
    border-bottom: 2px solid transparent;
    margin-right: 3px;
}}
QTabBar::tab:hover {{
    color: {TEXT};
    background: {BG_HOVER};
    border-radius: {RADIUS}px {RADIUS}px 0 0;
}}
QTabBar::tab:selected {{
    color: {ACCENT};
    font-weight: 600;
    border-bottom: 2px solid {ACCENT};
}}

/* ============ 分组框 ============ */
QGroupBox {{
    margin-top: 14px;
    padding: 14px 12px 10px;
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    background: {BG_PANEL};
    font-weight: 600;
    font-size: 10.5pt;
    color: {TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {ACCENT};
    background: {BG_PANEL};
}}

/* ---- 可折叠分组（PPT 侧边栏式） ---- */
QToolButton#collapseHeader {{
    background: transparent;
    border: 0;
    border-bottom: 1px solid {BORDER};
    border-radius: 0;
    text-align: left;
    padding: 6px 8px;
    font-weight: 600;
    font-size: 10.5pt;
    color: {TEXT};
    min-height: 28px;
}}
QToolButton#collapseHeader:hover {{
    background: {BG_HOVER};
    color: {ACCENT};
}}
QToolButton#collapseHeader:disabled {{
    color: {TEXT_FAINT};
    font-weight: 400;
    background: transparent;
}}
QToolButton#collapseHeader::menu-indicator {{
    image: none;
}}
QWidget#collapseContent {{
    background: transparent;
}}
QWidget#collapseContent:disabled {{
    background: transparent;
}}

/* ============ 输入控件（统一 30px 高） ============ */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    min-height: {CTRL_H}px;
    padding: 3px 10px;
    border: 1px solid {BORDER_LIGHT};
    border-radius: {RADIUS}px;
    background: {BG_PANEL};
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: {ON_ACCENT};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QTreeWidget:focus, QSlider:focus {{
    border: 1px solid {ACCENT};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background: {BG_RAISED};
    color: {TEXT_FAINT};
    border-color: {BORDER};
}}
QComboBox::drop-down {{
    border: 0;
    width: 26px;
}}
QComboBox::down-arrow {{
    image: url("{_ARROW_DOWN}");
    width: 10px;
    height: 6px;
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 4px;
    outline: 0;
    selection-background-color: {ACCENT_BG};
    selection-color: {TEXT};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    height: 12px;
    border: 0;
    background: transparent;
    border-top-right-radius: 4px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    height: 12px;
    border: 0;
    background: transparent;
    border-bottom-right-radius: 4px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {BG_HOVER};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{_ARROW_UP}");
    width: 10px;
    height: 6px;
    margin: 2px auto;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{_ARROW_DOWN}");
    width: 10px;
    height: 6px;
    margin: 2px auto;
}}

/* ============ 复选框 / 单选框 ============ */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {TEXT};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_LIGHT};
    border-radius: 4px;
    background: {BG_PANEL};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QRadioButton::indicator {{
    border-radius: 8px;
}}
QRadioButton::indicator:checked {{
    background: {ACCENT};
    border: 3px solid {BG_PANEL};
    outline: 1px solid {ACCENT};
}}

/* ============ 滑块 ============ */
QSlider::groove:horizontal {{
    height: 5px;
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_LIGHT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 17px;
    height: 17px;
    margin: -7px 0;
    border-radius: 9px;
    background: {BG_PANEL};
    border: 2px solid {ACCENT};
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_BG};
}}

/* ============ 分割条 ============ */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:hover {{
    background: {ACCENT_LIGHT};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}

/* ============ 状态栏 ============ */
QStatusBar {{
    background: {BG_WINDOW};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
    padding: 4px 12px;
}}
QStatusBar::item {{
    border: 0;
}}

/* ============ 滚动条 ============ */
QScrollBar:vertical {{
    background: transparent;
    width: 11px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_LIGHT};
    border-radius: 5px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_LIGHT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 11px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_LIGHT};
    border-radius: 5px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT_LIGHT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: transparent;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ============ Dock ============ */
QDockWidget {{
    color: {TEXT};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {BG_RAISED};
    padding: 8px 12px;
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px {RADIUS}px 0 0;
    font-weight: 600;
    color: {ACCENT};
}}

/* ============ matplotlib 工具栏（浅色自然融合） ============ */
QToolBar#matplotlibToolbar {{
    background: {BG_RAISED};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    spacing: 1px;
    padding: 3px 6px;
}}
QToolBar#matplotlibToolbar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 3px 5px;
    min-height: 24px;
}}
QToolBar#matplotlibToolbar QToolButton:hover {{
    background: {BG_HOVER};
    border: 1px solid {BORDER_LIGHT};
}}
QToolBar#matplotlibToolbar QToolButton:pressed {{
    background: {BG_ACTIVE};
}}

/* ============ 标签变体（三级字号：标题 12pt / 正文 10pt / 辅助 9pt） ============ */
QLabel#emptyState {{
    color: {TEXT_DIM};
    font-size: 12.5pt;
    background: transparent;
}}
QLabel#sectionTitle {{
    color: {ACCENT};
    font-weight: 700;
    font-size: 12pt;
    letter-spacing: 1px;
    padding: 0 0 5px 0;
    background: transparent;
    border-bottom: 2px solid {ACCENT};
}}
QLabel#timeValue {{
    color: {ACCENT};
    font-weight: 700;
    font-size: 12pt;
    background: transparent;
}}
QLabel#dimLabel {{
    color: {TEXT_DIM};
    font-size: 9.5pt;
    background: transparent;
}}
QFrame#metaSection {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}
QLabel#metaKey {{
    color: {TEXT_DIM};
    font-size: 9.5pt;
    background: transparent;
}}
QLabel#metaValue {{
    color: {TEXT};
    font-size: 10pt;
    background: transparent;
}}
QLabel#dimChip, QLabel#dimChipTime {{
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 9pt;
    font-weight: 600;
    background: {BG_HOVER};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
}}
QLabel#dimChipTime {{
    background: {ACCENT_BG};
    color: {ACCENT};
    border: 1px solid {ACCENT_LIGHT};
}}
QLabel#dimSize {{
    color: {ACCENT};
    font-weight: 700;
    font-size: 10.5pt;
    background: transparent;
}}
QLabel#dimPreview {{
    color: {TEXT_DIM};
    font-size: 9.5pt;
    background: transparent;
}}
QLabel#dimMeta {{
    color: {TEXT_FAINT};
    font-size: 9pt;
    background: transparent;
}}
/* ---- PyCharm Variables 风格（变量信息/维度信息） ---- */
QLabel#varTitle {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 17pt;
    font-weight: 700;
    color: {ACCENT};
    background: transparent;
    padding: 2px 0 0 0;
}}
QLabel#varSubtitle {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 9.5pt;
    color: {TEXT_DIM};
    background: transparent;
    padding-bottom: 2px;
}}
QLabel#varDim, QLabel#varDimTime {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 10pt;
    font-weight: 600;
    color: {TEXT};
    background: transparent;
}}
QLabel#varDimTime {{
    color: {ACCENT};
}}
QLabel#varDimSize {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 9.5pt;
    color: {TEXT_FAINT};
    background: transparent;
}}
QLabel#varDimPreview {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 9.5pt;
    color: {TEXT_DIM};
    background: transparent;
}}
QLabel#varDimMeta {{
    font-family: Consolas, Menlo, "Courier New", monospace;
    font-size: 9pt;
    color: {TEXT_FAINT};
    background: transparent;
}}
QLabel#rawInfo, QTextEdit#rawInfo {{
    background: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 8px;
    font-family: "Consolas", "Cascadia Mono", monospace;
    font-size: 9.5pt;
}}

/* ============ 提示框 ============ */
QToolTip {{
    background: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: {RADIUS}px;
    padding: 6px 9px;
}}
QMessageBox {{
    background: {BG_WINDOW};
}}
"""
