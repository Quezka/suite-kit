"""Keeping windows and dialogs inside the screen (a laptop at 1366x768 is small)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractButton, QDialog, QFrame, QMenu, QScrollArea, QVBoxLayout, QWidget

MARGIN = 24  # room left for the title bar and panels


def available(widget: QWidget | None = None):
    screen = (widget.screen() if widget is not None else None) or QGuiApplication.primaryScreen()
    return screen.availableGeometry() if screen else None


def clamp_window(window: QWidget, width: int, height: int, min_width: int, min_height: int):
    """Size a window as asked, but never bigger than the screen."""
    area = available(window)
    if area is None:
        window.resize(width, height)
        window.setMinimumSize(min_width, min_height)
        return
    max_w, max_h = area.width() - MARGIN, area.height() - MARGIN
    window.setMinimumSize(min(min_width, max_w), min(min_height, max_h))
    window.resize(min(width, max_w), min(height, max_h))


def clamp_dialog(dialog: QWidget, width: int, height: int):
    area = available(dialog)
    if area is None:
        dialog.resize(width, height)
        return
    dialog.resize(min(width, area.width() - MARGIN * 2), min(height, int(area.height() * 0.9)))


def scrollable(dialog: QDialog):
    """Put what the dialog shows in a scroll area, sized to fit the screen: a tall dialog
    scrolls instead of running off the bottom. Call it once the dialog is fully built."""
    layout = dialog.layout()
    content = QWidget()
    holder = QWidget()
    holder.setLayout(layout)  # a layout belongs to one widget: detach it first
    content.setLayout(layout)
    del holder
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.addWidget(scroll)
    hint = content.sizeHint()
    area = available(dialog)
    width = max(hint.width() + 18, dialog.minimumWidth())  # room for the scroll bar
    height = hint.height() + 4
    if area is not None:
        width = min(width, area.width() - MARGIN * 2)
        height = min(height, int(area.height() * 0.9))
        dialog.setMinimumWidth(min(dialog.minimumWidth(), width))
    dialog.setProperty("fitted", True)
    dialog.resize(width, height)


_STANDARD = ("QMessageBox", "QFileDialog", "QColorDialog", "QInputDialog", "QFontDialog",
             "QProgressDialog", "QErrorMessage")


class _Fitter(QObject):
    """Safety net: a dialog that would be taller than the screen scrolls instead. Done as the
    dialog is polished, just before it first appears (never while it's on screen)."""

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Polish and isinstance(obj, QDialog)
                and not obj.property("fitted")
                and not any(c.__name__ in _STANDARD for c in type(obj).__mro__)
                and obj.layout() is not None):
            obj.setProperty("fitted", True)
            from .settings import shape
            shape(obj)
            area = available(obj)
            if area is not None and obj.sizeHint().height() > int(area.height() * 0.9):
                scrollable(obj)
        return False


MENU_GAP = 3  # pixels between a button and the menu it opens


def menu_position(button_left: int, button_top: int, button_bottom: int, width: int, height: int, area) -> QPoint:
    """Where a button's menu goes: under the button with their left edges lined up, above it when there is
    no room below (a button at the bottom of the window), and never off the screen."""
    x = max(area.left(), min(button_left, area.right() + 1 - width))
    y = button_bottom + MENU_GAP
    if y + height > area.bottom() + 1 and button_top - MENU_GAP - height >= area.top():
        y = button_top - MENU_GAP - height
    return QPoint(x, max(area.top(), min(y, area.bottom() + 1 - height)))


class _MenuAligner(QObject):
    """Qt puts a button's menu roughly under it, a few pixels off depending on the style and the scale. The
    position is set while the menu is being shown, before the window exists on screen: on Wayland it can't
    be moved afterwards."""

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show and isinstance(watched, QMenu):
            button = watched.parent()
            if isinstance(button, QAbstractButton) and button.menu() is watched:
                top_left = button.mapToGlobal(QPoint(0, 0))
                size = watched.sizeHint()
                area = button.screen().availableGeometry()
                watched.move(menu_position(top_left.x(), top_left.y(), top_left.y() + button.height(),
                                           size.width(), size.height(), area))
        return False


def install(app) -> None:
    """Watch every dialog the app shows (see _Fitter) and every menu a button opens (see _MenuAligner)."""
    fitter = _Fitter(app)
    app.installEventFilter(fitter)
    app._dialog_fitter = fitter  # keep it alive
    aligner = _MenuAligner(app)
    app.installEventFilter(aligner)
    app._menu_aligner = aligner
