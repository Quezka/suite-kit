"""What's left of the old glass layer: the floating page header (solid since 0.13: Material 3, no blur) and the
shared outer edges of pages and sidebars. Apps that were on GNOME Blur my Shell's list are taken off it: its blur
costs the compositor on every frame.
"""
from __future__ import annotations

import os
import shutil
import subprocess

from PySide6.QtCore import QEvent, QObject, QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QScrollArea, QVBoxLayout, QWidget

from . import theme

BLUR_MY_SHELL = "blur-my-shell@aunetx"
BLUR_MY_SHELL_APPS = "org.gnome.shell.extensions.blur-my-shell.applications"


class GlassHeader(QWidget):
    """A header that floats over the top of a scroll area, inset like the cards: once the content scrolls under it,
    it gets a solid surface (Material 3's top app bar on scroll). Put widgets in `layout`. The scroll area's content
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
        # m3 top app bar: no fill @ top; surface fill once content scroll under
        if self.area.verticalScrollBar().value() <= 0:
            return
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), theme.OUTER_RADIUS, theme.OUTER_RADIUS)
        painter.fillPath(path, QColor(t.surface))
        painter.end()


Header = GlassHeader  # the name to use from 0.13 on


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


def leave_blur_my_shell(app_id: str) -> bool:
    """Takes the app off Blur my Shell's list. Its blur behind a window is redone by the compositor on every frame,
    even when the window is opaque and nothing shows through, so an app that isn't see-through must not be on it
    (the user saw scrolling and moving windows lag with see-through switched off). True if it's off the list."""
    if not app_id:
        return False
    current = _gsettings("get", BLUR_MY_SHELL_APPS, "whitelist")
    if current is None:
        return False
    if f"'{app_id}'" not in current:
        return True
    names = [n.strip().strip("'") for n in current.strip("@as []").split(",") if n.strip().strip("'")]
    names = [n for n in names if n != app_id]
    listed = "[" + ", ".join(f"'{n}'" for n in names) + "]"
    return _gsettings("set", BLUR_MY_SHELL_APPS, "whitelist", listed) is not None


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
    """Lines up pages and sidebars (see _Edges). `see_through` is ignored (kept so old callers still work)."""
    edges = _Edges(app)
    app.installEventFilter(edges)
    app._glass_edges = edges
    if "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper():
        # 0.12 and older put see-through apps on Blur my Shell's list: take this one off it
        leave_blur_my_shell(QApplication.desktopFileName())
