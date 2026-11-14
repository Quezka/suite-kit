"""Keeping windows and dialogs inside the screen (a laptop at 1366x768 is small)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt
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


def on_wayland() -> bool:
    return QGuiApplication.platformName().startswith("wayland")


# wayland: client no know window pos (qt use fake `(0,0)`) -> qt clamp menu to screen = wrong shift
# => @ wayland no clamp; compositor slide/flip popup @ real screen
_NO_CLAMP = QRect(-(1 << 20), -(1 << 20), 1 << 21, 1 << 21)
TARGET = "quezka_menu_target"
# xdg_positioner: slide_x 1 + slide_y 2 + flip_x 4 + flip_y 8 => compositor flip | slide menu @ screen edge
FLIP_OR_SLIDE = 1 | 2 | 4 | 8


def _let_compositor_fit(menu: QMenu) -> None:
    # read by qt wayland when popup role made = after show event => set here ok
    handle = menu.windowHandle()
    if handle is not None:
        handle.setProperty("_q_waylandPopupConstraintAdjustment", FLIP_OR_SLIDE)


def exec_menu(menu: QMenu, pos: QPoint):
    """Open a menu at a point (global coordinates, as mapToGlobal gives), exactly there."""
    menu.setProperty(TARGET, pos)
    return menu.exec(pos)


def popup_menu(menu: QMenu, pos: QPoint) -> None:
    """Like exec_menu, without waiting for a choice."""
    menu.setProperty(TARGET, pos)
    menu.popup(pos)


class _MenuAligner(QObject):
    """Qt puts a button's menu roughly under it, a few pixels off depending on the style and the scale. The
    position is set while the menu is being shown, before the window exists on screen: on Wayland it can't
    be moved afterwards. A menu opened with exec_menu goes back to the point asked for: Qt moved it to keep
    it on a screen whose position it doesn't know on Wayland."""

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Show and isinstance(watched, QMenu):
            button = watched.parent()
            target = watched.property(TARGET)
            if isinstance(target, QPoint):
                watched.setProperty(TARGET, None)
                if on_wayland():
                    _let_compositor_fit(watched)
                    watched.move(target)
            elif isinstance(button, QAbstractButton) and button.menu() is watched:
                top_left = button.mapToGlobal(QPoint(0, 0))
                size = watched.sizeHint()
                wayland = on_wayland()
                if wayland:
                    _let_compositor_fit(watched)
                area = _NO_CLAMP if wayland else button.screen().availableGeometry()
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


SIDEBAR_MAX = 280  # a long translated title still leaves room for the page
COMPACT_WIDTH = 56
COMPACT_BELOW = 1000  # window width below which a sidebar shows only icons


class _SidebarFit(QObject):
    """Keeps a sidebar as wide as its widest text needs (never under its base width), and
    icons-only while its window is narrow. The width is measured, not guessed: a title in a
    bigger font or another language still fits."""

    def __init__(self, frame: QFrame, base: int, compact_below: int | None):
        super().__init__(frame)
        self.frame, self.base, self.compact_below = frame, base, compact_below
        self.compact = False
        frame.installEventFilter(self)
        self._window = None

    def wide_width(self) -> int:
        frame = self.frame
        for child in frame.findChildren(QWidget):
            child.ensurePolished()
        layout = frame.layout()
        hint = layout.sizeHint().width() if layout is not None else 0
        return max(self.base, min(hint, SIDEBAR_MAX))

    def set_compact(self, compact: bool):
        from PySide6.QtWidgets import QLabel, QToolButton
        self.compact = compact
        for label in self.frame.findChildren(QLabel):
            if label.text():  # the title and any other words; the icon (a picture) stays
                label.setVisible(not compact)
        for button in self.frame.findChildren(QToolButton, "nav"):
            button.setToolButtonStyle(Qt.ToolButtonIconOnly if compact else Qt.ToolButtonTextBesideIcon)
        self.apply()

    def apply(self):
        width = COMPACT_WIDTH if self.compact else self.wide_width()
        if self.frame.width() != width or self.frame.minimumWidth() != width:
            self.frame.setFixedWidth(width)

    def eventFilter(self, watched, event):
        kind = event.type()
        if watched is self.frame:
            if kind == QEvent.Show and self._window is None and self.compact_below:
                self._window = self.frame.window()
                self._window.installEventFilter(self)
                self.set_compact(self._window.width() < self.compact_below)
            elif kind in (QEvent.Show, QEvent.LayoutRequest, QEvent.LanguageChange,
                          QEvent.StyleChange, QEvent.FontChange) and not self.compact:
                self.apply()
        elif kind == QEvent.Resize and self.compact_below:
            compact = watched.width() < self.compact_below
            if compact != self.compact:
                self.set_compact(compact)
        return False


def fit_sidebar(frame: QFrame, base: int, *, compact_below: int | None = COMPACT_BELOW) -> _SidebarFit:
    """Size a sidebar to its content (see _SidebarFit). Call once its layout is set."""
    frame.setFixedWidth(base)
    fit = _SidebarFit(frame, base, compact_below)
    frame._sidebar_fit = fit  # keep it alive
    return fit


# material 3 window size class; width in logical px
COMPACT, MEDIUM, EXPANDED = "compact", "medium", "expanded"


def size_class(width: int) -> str:
    """The window's size class: compact under 600 px, medium under 1000, expanded above."""
    return COMPACT if width < 600 else MEDIUM if width < COMPACT_BELOW else EXPANDED


class _SizeClassWatch(QObject):
    def __init__(self, widget: QWidget, callback):
        super().__init__(widget)
        self.callback, self.current = callback, None
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Resize, QEvent.Show):
            now = size_class(watched.width())
            if now != self.current:
                self.current = now
                self.callback(now)
        return False


def on_size_class(widget: QWidget, callback) -> None:
    """Call `callback(size_class)` when the widget is first shown and each time its size class changes,
    so a page can rearrange itself (stack its columns, hide a side panel) instead of squeezing."""
    widget._size_class_watch = _SizeClassWatch(widget, callback)
