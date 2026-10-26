"""Starting a Qt application the way every app in the suite does."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import fit, i18n, icons, leave_on_enter, theme, uiscale


def create_application(argv: list[str], *, name: str, app_id: str, icon: Path,
                       locale_package: str) -> QApplication:
    """The application object, set up in the order that matters: the scale factor before Qt reads it,
    the language before any window is built, the theme before any widget exists."""
    icons.configure(icon, name.lower())
    i18n.configure(locale_package)
    QApplication.setApplicationName(name)
    QApplication.setOrganizationName(name)
    QApplication.setDesktopFileName(app_id)
    if QApplication.instance() is None:
        uiscale.apply_before_app()
    app = QApplication.instance() or QApplication(argv)
    app.setStyle("Fusion")
    leave_on_enter.install(app)  # Enter in a one-line box lets go of it
    fit.install(app)  # a dialog taller than the screen scrolls
    app.setWindowIcon(QIcon(str(icon)))
    i18n.install(app=app)
    theme.install(app)
    return app
