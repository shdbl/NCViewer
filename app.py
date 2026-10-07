"""NCViewer 应用入口。"""
from __future__ import annotations

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
    apply_app_style(app)
    window = MainWindow()
    if len(sys.argv) > 1:
        window.open_file(sys.argv[1])
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
