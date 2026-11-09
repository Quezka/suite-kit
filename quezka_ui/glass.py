"""Liquid glass, the way Apple does it: backgrounds stay plain, and the chrome that floats over content is glass.
Menus, the lists that drop down from a box, tooltips and sticky headers blur what is really under them, with a
light edge on top. Nothing here invents a background: what shows through is the app's own content.

See-through windows (Windows Aero, macOS sidebars): where the desktop can blur what's behind a window, the main
windows and dialogs let it show through. On Windows that's the system's Acrylic (Windows 11) or its blur-behind
(Windows 10). On GNOME no app can ask for it; the Blur my Shell extension does it for the apps on its list, so when
it's installed the kit puts the app on that list. Cards stay solid either way.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMenu, QScrollArea, QVBoxLayout, QWidget

from . import theme

POPUP_RADIUS = theme.POPUP_RADIUS
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
            radius = POPUP_RADIUS - theme.POPUP_PADDING if obj.metaObject().className() == "QTipLabel" else POPUP_RADIUS
            paint_glass(painter, QRectF(obj.rect()), getattr(obj, "_glass_backdrop", None), radius)
            painter.end()
        return False


class GlassHeader(QWidget):
    """A header that floats over the top of a scroll area, inset like the cards: the content scrolls under it and
    shows through, blurred, once there's something under it. Put widgets in `layout`. The scroll area's content
    should start below it (see `header_height`); `inset` is the gap to the scroll area's top, left and right."""

    def __init__(self, area: QScrollArea, parent: QWidget, inset: tuple[int, int, int] = (0, theme.GAP, theme.GAP)):
        super().__init__(parent)
        self.area = area
        self.inset = inset  # left, top, right
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(theme.CARD_PADDING + 4, 12, theme.CARD_PADDING + 4, 12)
        area.verticalScrollBar().valueChanged.connect(lambda _v: self.update())
        # The scroll bar appearing narrows the cards (and the viewport): follow them.
        area.viewport().installEventFilter(self)
        theme.themed(lambda _t: self.update())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize and obj is self.area.viewport():
            self.place()
        return False

    def header_height(self) -> int:
        return self.sizeHint().height()

    def bottom(self) -> int:
        """Where the content should start: below the header and one gap."""
        return self.inset[1] + self.header_height() + theme.GAP

    def place(self):
        """Over the top of the scroll area, as wide as the cards (call from the parent's resizeEvent)."""
        left, top, right = self.inset
        viewport = self.area.viewport()
        top_left = viewport.mapTo(self.parentWidget(), QPoint(0, 0))
        width = viewport.width() - left - right
        self.setGeometry(top_left.x() + left, top_left.y() + top, max(width, 40), self.header_height())
        self.raise_()

    def paintEvent(self, _event):
        t = theme.current()
        scrolled = self.area.verticalScrollBar().value() > 0
        if not (theme.glass_on(t) and scrolled):
            return  # nothing under it yet: just the words on the background
        painter = QPainter(self)
        viewport = self.area.viewport()
        origin = viewport.mapFrom(self, QPoint(0, 0))
        shot = viewport.grab(QRect(origin, self.size())).toImage()
        paint_glass(painter, QRectF(self.rect()), blur(shot, 8), theme.OUTER_RADIUS, t)
        painter.end()


# ---- See-through windows ----------------------------------------------------------------------------------------

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic: the desktop behind, blurred
ACRYLIC_BUILD = 22621  # Windows 11 22H2: the first with a documented backdrop type
BLUR_BEHIND_BUILD = 17134  # Windows 10 1803: blur behind through the accent policy
BLUR_MY_SHELL = "blur-my-shell@aunetx"
BLUR_MY_SHELL_APPS = "org.gnome.shell.extensions.blur-my-shell.applications"


def windows_build() -> int:
    if sys.platform != "win32":
        return 0
    try:
        return sys.getwindowsversion().build
    except AttributeError:
        return 0


def _gsettings(*args: str) -> str | None:
    """Runs gsettings (with Blur my Shell's own schemas when it's installed per user); None if that fails."""
    exe = shutil.which("gsettings")
    if not exe:
        return None
    command = [exe]
    schemas = os.path.expanduser(f"~/.local/share/gnome-shell/extensions/{BLUR_MY_SHELL}/schemas")
    if "blur-my-shell" in " ".join(args) and os.path.isdir(schemas):
        command += ["--schemadir", schemas]
    try:
        done = subprocess.run(command + list(args), capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def blur_my_shell_on() -> bool:
    """Whether GNOME's Blur my Shell extension is switched on (it can blur what's behind chosen apps)."""
    if "GNOME" not in os.environ.get("XDG_CURRENT_DESKTOP", "").upper():
        return False
    enabled = _gsettings("get", "org.gnome.shell", "enabled-extensions") or ""
    return BLUR_MY_SHELL in enabled


def see_through_possible() -> bool:
    forced = os.environ.get("QUEZKA_SEE_THROUGH")
    if forced in ("0", "1"):
        return forced == "1"
    if sys.platform == "win32":
        return windows_build() >= BLUR_BEHIND_BUILD
    return blur_my_shell_on()


def join_blur_my_shell(app_id: str) -> bool:
    """Puts the app on Blur my Shell's list of apps it blurs behind, and switches that part on. True if it's there."""
    if not app_id:
        return False
    current = _gsettings("get", BLUR_MY_SHELL_APPS, "whitelist")
    if current is None:
        return False
    if f"'{app_id}'" not in current:
        names = [n.strip().strip("'") for n in current.strip("@as []").split(",") if n.strip().strip("'")]
        names.append(app_id)
        listed = "[" + ", ".join(f"'{n}'" for n in names) + "]"
        if _gsettings("set", BLUR_MY_SHELL_APPS, "whitelist", listed) is None:
            return False
    _gsettings("set", BLUR_MY_SHELL_APPS, "blur", "true")
    # Blur my Shell can also fade whole windows, words and all. The app makes its own background see-through, so
    # the window itself stays fully opaque.
    _gsettings("set", BLUR_MY_SHELL_APPS, "opacity", "255")
    return True


def apply_backdrop(window: QWidget, dark: bool) -> bool:
    """Asks Windows to blur the desktop behind `window`; True if it agreed. Its background must be see-through."""
    build = windows_build()
    if build < BLUR_BEHIND_BUILD:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(window.winId())
        if build >= ACRYLIC_BUILD:
            dwm = ctypes.windll.dwmapi
            value = ctypes.c_int(1 if dark else 0)
            dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
            backdrop = ctypes.c_int(DWMSBT_TRANSIENTWINDOW)
            return dwm.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop),
                                             ctypes.sizeof(backdrop)) == 0

        class Accent(ctypes.Structure):
            _fields_ = [("state", ctypes.c_int), ("flags", ctypes.c_int), ("colour", ctypes.c_uint),
                        ("animation", ctypes.c_int)]

        class Data(ctypes.Structure):
            _fields_ = [("attribute", ctypes.c_int), ("data", ctypes.c_void_p), ("size", ctypes.c_size_t)]

        accent = Accent(3, 0, 0, 0)  # ACCENT_ENABLE_BLURBEHIND
        data = Data(19, ctypes.cast(ctypes.byref(accent), ctypes.c_void_p), ctypes.sizeof(accent))  # WCA_ACCENT_POLICY
        call = ctypes.windll.user32.SetWindowCompositionAttribute
        call.argtypes = [wintypes.HWND, ctypes.POINTER(Data)]
        return bool(call(hwnd, ctypes.byref(data)))
    except Exception:
        return False


def _is_window(obj) -> bool:
    return isinstance(obj, (QMainWindow, QDialog)) and obj.isWindow()


class _SeeThrough(QObject):
    """Makes each main window and dialog see-through as it's first polished (and asks Windows for its blur)."""

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Polish and _is_window(obj) and obj.property("seeThrough") is None:
            on = theme.see_through_on(theme.current())
            obj.setProperty("seeThrough", on)
            if on:
                obj.setAttribute(Qt.WA_TranslucentBackground, True)
        elif kind == QEvent.Paint and _is_window(obj) and obj.property("seeThrough") is True:
            # Qt skips a see-through window's own background, so it's painted here, before the window's content.
            t = theme.current()
            if theme.see_through_on(t):
                painter = QPainter(obj)
                painter.fillRect(obj.rect(), QColor(theme.see_through_fill(t)))
                painter.end()
        elif kind == QEvent.Show and _is_window(obj) and obj.property("seeThrough") is True and sys.platform == "win32":
            if not apply_backdrop(obj, theme.current().dark):
                obj.setAttribute(Qt.WA_TranslucentBackground, False)
        return False


def _layout_holding(widget: QWidget):
    """The layout `widget` sits in directly (searched through its parent's nested layouts), or None."""
    parent = widget.parentWidget()
    if parent is None or parent.layout() is None:
        return None
    todo = [parent.layout()]
    while todo:
        layout = todo.pop()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() is widget:
                return layout
            if item.layout() is not None:
                todo.append(item.layout())
    return None


class _Edges(QObject):
    """Lines every app's pages and sidebar up the same way, as they're first polished: pages sit one GAP from the
    sidebar and from the window's right and bottom edges (where the floating sidebar ends too), and the sidebar's
    buttons sit NAV_PADDING inside it, so their corners nest in its corners."""

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Polish or not isinstance(obj, QWidget) or obj.property("edges"):
            return False
        name = obj.objectName()
        if name == "card":
            # Cards side by side or one above another sit one GAP apart, like the page's edges.
            holder = _layout_holding(obj)
            if holder is not None and holder.spacing() > theme.GAP:
                holder.setSpacing(theme.GAP)
            return False
        if name not in ("page", "sidebar"):
            return False
        layout = obj.layout()
        if layout is None:
            return False
        obj.setProperty("edges", True)
        m = layout.contentsMargins()
        if name == "page":
            layout.setContentsMargins(theme.GAP, m.top(), theme.GAP, theme.GAP)
            layout.setSpacing(theme.GAP)
        else:
            layout.setContentsMargins(theme.NAV_PADDING, m.top(), theme.NAV_PADDING, max(m.bottom(), theme.NAV_PADDING))
        return False


def install(app, see_through: bool = True) -> None:
    """`see_through=False` for an app whose windows should never let the desktop through (a 3D viewer)."""
    edges = _Edges(app)
    app.installEventFilter(edges)
    app._glass_edges = edges
    popups = _Popups(app)
    app.installEventFilter(popups)
    app._glass_popups = popups  # keep it alive
    theme.SEE_THROUGH_POSSIBLE = see_through and see_through_possible()
    if theme.SEE_THROUGH_POSSIBLE:
        if sys.platform != "win32" and theme.SEE_THROUGH:
            join_blur_my_shell(QApplication.desktopFileName())
        windows = _SeeThrough(app)
        app.installEventFilter(windows)
        app._glass_windows = windows
