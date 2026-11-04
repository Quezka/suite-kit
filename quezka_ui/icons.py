"""Icons tinted at runtime to match the theme: Material Symbols (`symbols.py`, Apache 2.0, regenerate with
tools/make_symbols.py), outlined normally and filled when selected, as Material 3 has it.

A few have no Material symbol because they are a notation, not a picture: an ER entity is a box, a relationship
a diamond. Those stay as line drawings (`_PATHS`, adapted from Feather Icons, MIT licence).
"""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from . import symbols

# Each app points this at its own icon (see `configure`).
APP_ICON = Path(__file__).resolve().parent / "assets" / "icon.svg"

_PATHS = {
    'attribute': '<circle cx="12" cy="7" r="3"/><path d="M12 10v11"/>',
    'class': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16"/>',
    'entity': '<rect x="3" y="6" width="18" height="12" rx="2"/>',
    'inherit': '<path d="M12 21V9"/><path d="M6 10l6-7 6 7z"/>',
    'relationship': '<path d="M12 3l9 9-9 9-9-9z"/>',
}


def names() -> set[str]:
    return set(symbols.OUTLINED) | set(_PATHS)


def svg(name: str, color: str, stroke: float = 2.0, filled: bool = False) -> str:
    if name in symbols.OUTLINED:
        path = symbols.FILLED.get(name) if filled else None
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" '
                f'fill="{color}"><path d="{path or symbols.OUTLINED[name]}"/></svg>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{_PATHS[name]}</svg>')


def pixmap(name: str, color: str, size: int = 16, stroke: float = 2.0, filled: bool = False) -> QPixmap:
    app = QGuiApplication.instance()
    ratio = app.devicePixelRatio() if app else 1.0
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.fill(Qt.transparent)
    renderer = QSvgRenderer(QByteArray(svg(name, color, stroke, filled).encode()))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, pm.width(), pm.height()))
    painter.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def icon(name: str, color: str, checked_color: str | None = None, size: int = 16,
         disabled_color: str | None = None) -> QIcon:
    result = QIcon(pixmap(name, color, size))
    if checked_color:
        result.addPixmap(pixmap(name, checked_color, size, filled=True), QIcon.Normal, QIcon.On)
    if disabled_color:
        for state in (QIcon.Off, QIcon.On):
            result.addPixmap(pixmap(name, disabled_color, size), QIcon.Disabled, state)
    return result


_CACHE = Path(tempfile.gettempdir()) / "quezka-ui-icons"


def configure(app_icon: Path, cache_name: str | None = None) -> None:
    """Tell the kit which icon is the app's, and where its tinted icon files go."""
    global APP_ICON, _CACHE
    APP_ICON = Path(app_icon)
    if cache_name:
        _CACHE = Path(tempfile.gettempdir()) / f"{cache_name}-icons"


def register(extra: dict[str, str]) -> None:
    """Add icons of the app's own, as line drawings (a name that exists already must keep its drawing; a name with
    a Material symbol has that symbol)."""
    for name, drawing in extra.items():
        if name in symbols.OUTLINED:
            continue
        if _PATHS.setdefault(name, drawing) != drawing:
            raise ValueError(f"icon {name!r} already exists with another drawing")


def icon_file(name: str, color: str, stroke: float = 2.0) -> str:
    """An SVG file on disk, for style sheets that need url(...) images."""
    data = svg(name, color, stroke)
    _CACHE.mkdir(exist_ok=True)
    path = _CACHE / f"{name}-{hashlib.sha1(data.encode()).hexdigest()[:10]}.svg"
    if not path.exists():
        path.write_text(data, encoding="utf-8")
    return path.as_posix()
