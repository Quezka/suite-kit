"""Liquid glass, the way Apple does it: backgrounds stay plain, and the chrome that floats over content is glass.
Menus, the lists that drop down from a box, tooltips and sticky headers blur what is really under them, with a
light edge on top. Nothing here invents a background: what shows through is the app's own content.

On Windows 11 the main window also gets the system's own Mica (a blur of the real desktop), and the sidebar lets it
show through, as Windows' own apps do.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QMainWindow, QMenu, QScrollArea, QVBoxLayout, QWidget

from . import theme

POPUP_RADIUS = 14
BLUR_STEPS = 9  # how much the backdrop is shrunk before it's stretched back: the blur's strength


def blur(image: QImage, steps: int = BLUR_STEPS) -> QImage:
    """A soft blur: shrinking the picture and stretching it back, twice, with smooth scaling. Cheap enough to run
    every time a menu opens or a header repaints."""
    if image.isNull() or image.width() < 2 or image.height() < 2:
        return image
    w, h = image.width(), image.height()
    small = image.scaled(max(1, w // steps), max(1, h // steps), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    small = small.scaled(max(1, w // (steps * 2)), max(1, h // (steps * 2)), Qt.IgnoreAspectRatio,
                         Qt.SmoothTransformation)
    middle = small.scaled(max(1, w // 2), max(1, h // 2), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    return middle.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def paint_glass(painter: QPainter, rect: QRectF, backdrop: QImage | None, radius: float, t=None,
                strength: float = 1.0) -> None:
    """Glass over `backdrop` (what's behind, already blurred): the blur, a light tint so text stays readable, a
    bright line along the top edge and a fine outline."""
    t = t or theme.current()
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setClipPath(path)
    if backdrop is not None and not backdrop.isNull():
        painter.drawImage(rect, backdrop)
    tint = QColor(t.surface)
    tint.setAlphaF((0.55 if t.dark else 0.50) * strength + (1 - strength))
    painter.fillPath(path, tint)
    # The light catching the top edge.
    shine = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    top = QColor(255, 255, 255, 70 if t.dark else 150)
    clear = QColor(255, 255, 255, 0)
    shine.setColorAt(0.0, top)
    shine.setColorAt(min(1.0, 18.0 / max(rect.height(), 1.0)), clear)
    painter.fillPath(path, shine)
    painter.restore()
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    edge = QColor(255, 255, 255, 46) if t.dark else QColor(0, 0, 0, 34)
    painter.setPen(QPen(edge, 1))
    painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    painter.restore()


def _is_popup(widget: QWidget) -> bool:
    name = widget.metaObject().className()
    return isinstance(widget, QMenu) or name in ("QComboBoxPrivateContainer", "QTipLabel")


def _backdrop_for(popup: QWidget) -> QImage | None:
    """What the popup covers, taken from the window under it, blurred."""
    parent = popup.parentWidget()
    window = parent.window() if parent is not None else QApplication.activeWindow()
    if window is None or window is popup:
        return None
    area = QRect(window.mapFromGlobal(popup.mapToGlobal(QPoint(0, 0))), popup.size())
    shot = window.grab(area).toImage()
    return blur(shot) if not shot.isNull() else None


class _Popups(QObject):
    """Makes every menu, drop-down list and tooltip of the app glass, as they appear."""

    def eventFilter(self, obj, event):
        if not isinstance(obj, QWidget) or not theme.glass_on(theme.current()):
            return False
        kind = event.type()
        if kind == QEvent.Polish and _is_popup(obj) and not obj.property("glassy"):
            obj.setProperty("glassy", True)
            obj.setAttribute(Qt.WA_TranslucentBackground, True)
        elif kind == QEvent.Show and obj.property("glassy"):
            obj._glass_backdrop = _backdrop_for(obj)
        elif kind == QEvent.Paint and obj.property("glassy"):
            painter = QPainter(obj)
            radius = 8 if obj.metaObject().className() == "QTipLabel" else POPUP_RADIUS
            paint_glass(painter, QRectF(obj.rect()), getattr(obj, "_glass_backdrop", None), radius)
            painter.end()
        return False


class GlassHeader(QWidget):
    """A header that floats over the top of a scroll area: the content scrolls under it and shows through, blurred.
    Put widgets in `layout`. The scroll area's content should start below it (see `header_height`)."""

    def __init__(self, area: QScrollArea, parent: QWidget):
        super().__init__(parent)
        self.area = area
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(26, 16, 26, 12)
        area.verticalScrollBar().valueChanged.connect(lambda _v: self.update())
        theme.themed(lambda _t: self.update())

    def header_height(self) -> int:
        return self.sizeHint().height()

    def place(self):
        """Over the top of the scroll area, full width (call from the parent's resizeEvent)."""
        top_left = self.area.mapTo(self.parentWidget(), QPoint(0, 0))
        bar = self.area.verticalScrollBar()
        width = self.area.width() - (bar.width() if bar.isVisible() else 0)
        self.setGeometry(top_left.x(), top_left.y(), width, self.header_height())
        self.raise_()

    def paintEvent(self, _event):
        t = theme.current()
        painter = QPainter(self)
        scrolled = self.area.verticalScrollBar().value() > 0
        if theme.glass_on(t) and scrolled:
            viewport = self.area.viewport()
            shot = viewport.grab(QRect(QPoint(0, 0), self.size())).toImage()
            painter.drawImage(self.rect(), blur(shot, 8))
            tint = QColor(t.bg)
            tint.setAlphaF(0.58)
            painter.fillRect(self.rect(), tint)
            painter.setPen(QPen(QColor(255, 255, 255, 40) if t.dark else QColor(0, 0, 0, 30), 1))
            painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        else:
            painter.fillRect(self.rect(), QColor(t.bg))
        painter.end()


# ---- Windows 11: Mica behind the window -----------------------------------------------------------------------

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_MAINWINDOW = 2  # Mica
MICA_BUILD = 22621  # Windows 11 22H2: the first with a documented backdrop type


def windows_build() -> int:
    if sys.platform != "win32":
        return 0
    try:
        return sys.getwindowsversion().build
    except AttributeError:
        return 0


def mica_possible() -> bool:
    return windows_build() >= MICA_BUILD


def apply_mica(window: QWidget, dark: bool) -> bool:
    """Asks Windows for Mica behind `window`; True if it agreed. Its background must then be transparent."""
    if not mica_possible():
        return False
    try:
        import ctypes
        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi
        value = ctypes.c_int(1 if dark else 0)
        dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        backdrop = ctypes.c_int(DWMSBT_MAINWINDOW)
        return dwm.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop),
                                         ctypes.sizeof(backdrop)) == 0
    except Exception:
        return False


class _Mica(QObject):
    """Gives each main window Mica on Windows 11 (glass look on, high contrast off)."""

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Polish and isinstance(obj, QMainWindow) and not obj.property("mica")
                and theme.glass_on(theme.current())):
            obj.setProperty("mica", True)
            obj.setAttribute(Qt.WA_TranslucentBackground, True)
        elif event.type() == QEvent.Show and isinstance(obj, QMainWindow) and obj.property("mica") is True:
            if apply_mica(obj, theme.current().dark):
                obj.setProperty("mica", "on")
                obj.setStyleSheet("QMainWindow { background: transparent; } #sidebar { background: transparent; }")
            else:
                obj.setAttribute(Qt.WA_TranslucentBackground, False)
                obj.setProperty("mica", "off")
        return False


def install(app) -> None:
    popups = _Popups(app)
    app.installEventFilter(popups)
    app._glass_popups = popups  # keep it alive
    if mica_possible():
        mica = _Mica(app)
        app.installEventFilter(mica)
        app._glass_mica = mica
