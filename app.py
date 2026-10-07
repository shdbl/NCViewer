"""NCViewer 应用入口。"""
from __future__ import annotations

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PySide6.QtWidgets import QApplication
from ncviewer.ui.main_window import MainWindow
from ncviewer.ui.style import apply_app_style


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NCViewer")
    app.setOrganizationName("NCViewer")
    # 应用图标（打包后从 _MEIPASS 解析资源路径）
    _res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "resources")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        _res_dir = os.path.join(sys._MEIPASS, "ncviewer", "ui", "resources")
    _icon = os.path.join(_res_dir, "ncviewer.ico")
    if os.path.exists(_icon):
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(_icon))
    apply_app_style(app)
    window = MainWindow()
    if len(sys.argv) > 1:
        window.open_file(sys.argv[1])
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
