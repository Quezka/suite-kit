"""Starting a Qt application the way every app in the suite does."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import tokens, glass, fit, fonts, i18n, icons, kinetic, leave_on_enter, theme, uiscale


BASE_PT = tokens.pt('body')  # the suite's body size (16 px)
THEMED_CLASSES = ("QLabel", "QPushButton", "QToolButton", "QCheckBox", "QRadioButton", "QGroupBox", "QMenu",
                  "QMenuBar", "QAbstractItemView", "QListView", "QTreeView", "QTableView", "QListWidget", "QTreeWidget", "QTableWidget",
                  "QHeaderView", "QTabBar", "QComboBox", "QLineEdit",
                  "QTextEdit", "QPlainTextEdit", "QSpinBox", "QDoubleSpinBox", "QDateEdit", "QTimeEdit", "QStatusBar")


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
    family = fonts.load()
    font = app.font()  # compact: never bigger than BASE_PT, whatever the desktop's own text size
    if family:
        font.setFamily(family)
    font.setPointSizeF(min(font.pointSizeF(), BASE_PT) if font.pointSizeF() > 0 else BASE_PT)
    app.setFont(font)
    leave_on_enter.install(app)  # Enter in a one-line box lets go of it
    fit.install(app)  # a dialog taller than the screen scrolls
    kinetic.install(app)  # a flick on a trackpad keeps gliding
    glass.install(app)  # glass menus, lists and tooltips; see-through windows where the desktop can blur
    app.setWindowIcon(QIcon(str(icon)))
    i18n.install(app=app)
    theme.install(app)
    # The desktop's theme gives these classes the system's own text size (11 pt on Ubuntu) whatever the
    # application font says, so each one is set explicitly, and last (styling the application resets them).
    for cls in THEMED_CLASSES:
        app.setFont(font, cls)
    return app
