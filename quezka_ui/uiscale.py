"""One scale for the whole interface, chosen in Settings (or automatic for small screens).

Qt reads the scale factor once, when the application is created, so this runs before that and
the choice applies after a restart. It scales everything alike (text, icons, fixed sizes).
"""
from __future__ import annotations

import gc
import os

from PySide6.QtCore import QSettings

MARK = "QUEZKA_UI_SCALE_APPLIED"  # the QT_SCALE_FACTOR we set ourselves, so a restart can replace it
CHOICES = ("auto", "80", "90", "100", "115", "130", "150", "175", "200")  # percent
STANDARD = 1.0  # "automatic" leaves Qt alone: the interface is built compact (see theme.py), not scaled


def chosen() -> str:
    value = str(QSettings().value("ui_scale", "auto"))
    return value if value in CHOICES else "auto"


def set_chosen(choice: str):
    QSettings().setValue("ui_scale", choice if choice in CHOICES else "auto")


def factor(choice: str, screen_height: int | None) -> float:
    """The scale factor for a choice; "auto" is no scaling, whatever the screen."""
    if choice == "auto":
        return STANDARD
    return int(choice) / 100 if choice in CHOICES else 1.0


def _screen_height() -> int | None:
    """The main screen's height, asked of a throwaway application (the real one can't be
    created until the scale is known)."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.instance() is not None:
        return None
    # Tearing the probe down forgets the names set before it, and the desktop file name is
    # what the desktop uses to put a window under its dock icon: put them back.
    names = (QCoreApplication.applicationName(), QCoreApplication.organizationName(),
             QGuiApplication.desktopFileName())
    probe = QGuiApplication([])
    try:
        screen = probe.primaryScreen()
        return screen.size().height() if screen else None
    finally:
        probe.shutdown()
        del probe
        gc.collect()
        QCoreApplication.setApplicationName(names[0])
        QCoreApplication.setOrganizationName(names[1])
        QGuiApplication.setDesktopFileName(names[2])


def apply_before_app():
    """Set QT_SCALE_FACTOR from the choice. Does nothing when you set it yourself on the command line.
    A value this function set earlier doesn't count as yours: a restart from Settings starts the new
    copy with this copy's environment, and the new choice must win over it."""
    current, ours = os.environ.get("QT_SCALE_FACTOR"), os.environ.get(MARK)
    if current is not None and current != ours:
        return
    value = factor(chosen(), None)
    if value != 1.0:
        os.environ["QT_SCALE_FACTOR"] = os.environ[MARK] = f"{value:g}"
    elif ours is not None:
        os.environ.pop("QT_SCALE_FACTOR", None)
        os.environ.pop(MARK, None)
