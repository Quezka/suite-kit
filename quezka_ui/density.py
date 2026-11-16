"""Text and padding that follow the window's size: on a small screen (a 1366x768 laptop, a window made small)
text and row heights tighten a bit (room around text stays) instead of being cut or squeezed; on a big one it stays as designed. Live: no restart.
Works on the stylesheet (font sizes in pt, padding/margin/height in px) and the application font."""
from __future__ import annotations

import re

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QMainWindow

# (min width, min height, factor): the first that fits wins
STEPS = ((1100, 760, 1.0), (900, 640, 0.92), (0, 0, 0.85))
_k = 1.0
# padding/margin/spacing never shrink <- user: text tight @ small screen; only text + heights follow k
_SIZE = re.compile(r"((?:min-height|max-height|height|min-width)[\w-]*\s*:\s*)([^;}]+)")
_PX = re.compile(r"(\d+(?:\.\d+)?)px")
_PT = re.compile(r"(font-size\s*:\s*)(\d+(?:\.\d+)?)pt")


def factor() -> float:
    return _k


def for_size(width: int, height: int) -> float:
    for w, h, k in STEPS:
        if width >= w and height >= h:
            return k
    return STEPS[-1][2]


def scale_css(css: str, k: float | None = None) -> str:
    """The stylesheet at density k: font sizes and heights scaled; paddings, margins, borders and radii kept."""
    k = _k if k is None else k
    if k == 1.0:
        return css
    css = _PT.sub(lambda m: f"{m[1]}{round(float(m[2]) * k, 2):g}pt", css)
    return _SIZE.sub(lambda m: m[1] + _PX.sub(lambda p: f"{max(1, round(float(p[1]) * k))}px", m[2]), css)


class _Watcher(QObject):
    """Watches main windows' sizes; a change of step re-applies the theme at the new density (debounced)."""

    def __init__(self, app, apply):
        super().__init__(app)
        self._apply = apply
        self._pending: float | None = None
        self._timer = QTimer(self, singleShot=True, interval=250)
        self._timer.timeout.connect(self._fire)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show) and isinstance(watched, QMainWindow) and watched.isVisible():
            k = for_size(watched.width(), watched.height())
            if k != _k:
                self._pending = k
                self._timer.start()
        return False

    def _fire(self):
        global _k
        if self._pending is not None and self._pending != _k:
            _k = self._pending
            self._apply()
        self._pending = None


def install(app, apply) -> None:
    """`apply()` restyles the app (theme manager); called after the density changes."""
    watcher = _Watcher(app, apply)
    app.installEventFilter(watcher)
    app._density_watcher = watcher
