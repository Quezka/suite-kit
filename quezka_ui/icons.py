"""Line icons drawn from inline SVG, tinted at runtime to match the theme.

Paths adapted from Feather Icons (MIT licence, https://feathericons.com).
"""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Each app points this at its own icon (see `configure`).
APP_ICON = Path(__file__).resolve().parent / "assets" / "icon.svg"

_PATHS = {
    'align': '<path d="M4 3v18M8 7h12M8 13h8M8 17h10"/>',
    'angle': '<path d="M4 20h16M4 20L16 5"/><path d="M11 20a7 7 0 0 0-1.6-4.4"/>',
    'arrow-down': '<path d="M12 5v14M19 12l-7 7-7-7"/>',
    'arrow-up': '<path d="M12 19V5M5 12l7-7 7 7"/>',
    'arrow-up-right': '<path d="M5 19L19 5"/><path d="M11 5h8v8"/>',
    'attribute': '<circle cx="12" cy="7" r="3"/><path d="M12 10v11"/>',
    'bell': '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    'bold': '<path d="M6 4h8a4 4 0 0 1 0 8H6zM6 12h9a4 4 0 0 1 0 8H6z"/>',
    'book': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    'book-open': '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    'briefcase': '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    'calendar': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    'calendar-day': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><rect x="8" y="14" width="4" height="4" rx="1"/>',
    'camera': '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
    'cards': '<rect x="2" y="6" width="15" height="14" rx="2"/><path d="M7 2h13a2 2 0 0 1 2 2v12"/>',
    'check': '<path d="M20 6L9 17l-5-5"/>',
    'checklist': '<path d="M3 5l2 2 4-4M3 15l2 2 4-4M13 6h8M13 16h8"/>',
    'chevron-down': '<path d="M6 9l6 6 6-6"/>',
    'chevron-left': '<path d="M15 18l-6-6 6-6"/>',
    'chevron-right': '<path d="M9 18l6-6-6-6"/>',
    'chevron-up': '<path d="M18 15l-6-6-6 6"/>',
    'circle': '<circle cx="12" cy="12" r="9"/><path d="M5.6 18.4l12.8-12.8"/>',
    'class': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16"/>',
    'code': '<path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>',
    'collapse': '<path d="M7 4l5 5 5-5M7 20l5-5 5 5"/>',
    'copy': '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    'coursework': '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    'critical': '<path d="M13 2L3 14h9l-1 8 10-12h-9z"/>',
    'csv': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8M12 9v0"/>',
    'cube': '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96L12 12.01l8.73-5.05M12 22.08V12"/>',
    'database': '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    'diagram': '<rect x="2" y="3" width="8" height="6" rx="1"/><rect x="14" y="15" width="8" height="6" rx="1"/><path d="M6 9v4a2 2 0 0 0 2 2h6"/>',
    'dimensions': '<path d="M21 3l-7 7M3 21l7-7M15 3h6v6M9 21H3v-6"/>',
    'distance': '<path d="M3 12h18M3 7v10M21 7v10"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    'drop': '<path d="M12 2.5C12 2.5 5 10 5 15a7 7 0 0 0 14 0c0-5-7-12.5-7-12.5z"/>',
    'edit': '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    'entity': '<rect x="3" y="6" width="18" height="12" rx="2"/>',
    'eye': '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8"/>',
    'fit': '<path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/>',
    'fit-day': '<path d="M7 15l5 5 5-5M7 9l5-5 5 5"/><path d="M4 12h16"/>',
    'flag': '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7"/>',
    'folder': '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    'form': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    'gantt': '<path d="M3 5h9M7 12h10M12 19h9"/><path d="M3 3v18"/>',
    'grid': '<path d="M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18"/>',
    'heading': '<path d="M6 4v16M18 4v16M6 12h12"/>',
    'home': '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    'image': '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>',
    'indent': '<path d="M3 6h18M11 12h10M11 18h10M3 9l3 3-3 3"/>',
    'inherit': '<path d="M12 21V9"/><path d="M6 10l6-7 6 7z"/>',
    'italic': '<path d="M19 4h-9M14 20H5M15 4L9 20"/>',
    'key': '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3L21 2M16 7l3 3M18 5l2 2"/>',
    'layers': '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
    'link': '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    'list': '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    'moon': '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    'more': '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    'notes': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    'outdent': '<path d="M3 6h18M11 12h10M11 18h10M6 9l-3 3 3 3"/>',
    'palette': '<circle cx="13.5" cy="6.5" r="1"/><circle cx="17.5" cy="10.5" r="1"/><circle cx="8.5" cy="7.5" r="1"/><circle cx="6.5" cy="12.5" r="1"/><path d="M12 2a10 10 0 0 0 0 20 2 2 0 0 0 2-2 2 2 0 0 1 2-2h2a4 4 0 0 0 4-4c0-6-4.5-12-10-12z"/>',
    'palm': '<path d="M12 22V10M12 10C9 10 6 8 5 4c4 0 7 2 7 6zM12 10c3 0 6-2 7-6-4 0-7 2-7 6z"/>',
    'pause': '<path d="M8 4v16M16 4v16"/>',
    'pin': '<path d="M12 17v5M9 10.76V6h6v4.76l2 3.24H7z"/><path d="M8 2h8"/>',
    'play': '<path d="M7 4l13 8-13 8z"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'pointer': '<path d="M4 3l7 17 2.5-7.5L21 10z"/><path d="M13.5 12.5L20 19"/>',
    'project': '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    'query': '<path d="M3 4h18l-7 8.5V19l-4 2v-8.5z"/>',
    'quote': '<path d="M3 21c3 0 7-1 7-8V5H3v7h4M14 21c3 0 7-1 7-8V5h-7v7h4"/>',
    'redo': '<path d="M15 14l5-5-5-5"/><path d="M20 9H9a5 5 0 0 0 0 10h3"/>',
    'refresh': '<path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/>',
    'relations': '<rect x="2" y="3" width="8" height="6" rx="1"/><rect x="14" y="15" width="8" height="6" rx="1"/><path d="M6 9v4a2 2 0 0 0 2 2h6"/>',
    'relationship': '<path d="M12 3l9 9-9 9-9-9z"/>',
    'report': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 18v-3M12 18v-6M16 18v-4"/>',
    'reset': '<path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"/><path d="M3 3v5h5"/>',
    'ruler': '<path d="M21.3 8.7L8.7 21.3a1 1 0 0 1-1.4 0L2.7 16.7a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4z"/><path d="M7.5 10.5l2 2M10.5 7.5l2 2M13.5 4.5l2 2M4.5 13.5l2 2"/>',
    'save': '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
    'school': '<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    'search': '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>',
    'section': '<path d="M3 12h18"/><path d="M5 8V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3M5 16v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"/>',
    'settings': '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    'shuffle': '<path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>',
    'side-panel': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/>',
    'skip': '<path d="M5 4l10 8-10 8zM19 5v14"/>',
    'star': '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
    'swap': '<path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    'table': '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    'tag': '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><circle cx="7" cy="7" r="1.5"/>',
    'target': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    'terminal': '<path d="M4 17l6-6-6-6M12 19h8"/>',
    'timer': '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6M12 2v3"/>',
    'today': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    'trash': '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    'undo': '<path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',
    'unlink': '<path d="M18.84 12.25l1.72-1.71a5 5 0 0 0-7.07-7.07l-1.72 1.71M5.17 11.75l-1.71 1.71a5 5 0 0 0 7.07 7.07l1.71-1.71M8 2v3M2 8h3M16 22v-3M22 16h-3"/>',
    'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>',
    'users': '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    'week': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    'x': '<path d="M18 6L6 18M6 6l12 12"/>',
    'zoom-in': '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35M11 8v6M8 11h6"/>',
    'zoom-out': '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35M8 11h6"/>',
}


def svg(name: str, color: str, stroke: float = 2.0) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{_PATHS[name]}</svg>')


def pixmap(name: str, color: str, size: int = 16, stroke: float = 2.0) -> QPixmap:
    app = QGuiApplication.instance()
    ratio = app.devicePixelRatio() if app else 1.0
    pm = QPixmap(int(size * ratio), int(size * ratio))
    pm.fill(Qt.transparent)
    renderer = QSvgRenderer(QByteArray(svg(name, color, stroke).encode()))
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
        result.addPixmap(pixmap(name, checked_color, size), QIcon.Normal, QIcon.On)
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
    """Add icons of the app's own (a name that exists already must keep its drawing)."""
    for name, drawing in extra.items():
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
