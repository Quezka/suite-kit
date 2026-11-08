"""Design tokens, palette and style sheet. Follows the system light/dark setting."""
from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from . import icons


@dataclass(frozen=True)
class Theme:
    dark: bool
    bg: str
    surface: str
    raised: str
    sidebar: str
    border: str
    hover: str
    text: str
    muted: str
    faint: str
    accent: str
    accent_hover: str
    accent_soft: str
    on_accent: str
    danger: str
    success: str
    warning: str = "#d97706"
    flag: str = "#e5484d"  # a brand's signature colour, used sparingly (the school's red in Gantry)


# Material 3 flavoured: tonal surfaces tinted by the accent, with dark text, firm borders where there are
# borders, and no pale grey for anything that matters.
LIGHT = Theme(
    dark=False,
    bg="#f3f2ff", surface="#ffffff", raised="#e9e8ff", sidebar="#eceaff",
    border="#b3b6cc", hover="#dedcf7",
    text="#0b0d14", muted="#343b4d", faint="#4d5466",
    accent="#4f46e5", accent_hover="#4338ca", accent_soft="#dcdbff", on_accent="#ffffff",
    danger="#d0262d", success="#127a46", warning="#b45309", flag="#d0262d",
)

DARK = Theme(
    dark=True,
    bg="#0e0e19", surface="#1a1a2b", raised="#27273f", sidebar="#13131f",
    border="#4b4e66", hover="#2d2d47",
    text="#f6f7fb", muted="#cbcfdd", faint="#a2a8bb",
    accent="#a9a6ff", accent_hover="#c3c0ff", accent_soft="#3b3984", on_accent="#0b0b14",
    danger="#ff7b80", success="#4ade80", warning="#fbbf24", flag="#ff7b80",
)

# "High contrast" in Settings: black on white / white on black, thick lines.
HIGH_LIGHT = Theme(
    dark=False,
    bg="#ffffff", surface="#ffffff", raised="#f0f0f0", sidebar="#f0f0f0",
    border="#000000", hover="#dcdcdc",
    text="#000000", muted="#1a1a1a", faint="#333333",
    accent="#1f1fa8", accent_hover="#14147a", accent_soft="#cfcff7", on_accent="#ffffff",
    danger="#a30000", success="#005a2b", warning="#7a4100", flag="#a30000",
)

HIGH_DARK = Theme(
    dark=True,
    bg="#000000", surface="#000000", raised="#1a1a1a", sidebar="#0a0a0a",
    border="#ffffff", hover="#2e2e2e",
    text="#ffffff", muted="#e6e6e6", faint="#cccccc",
    accent="#ffd400", accent_hover="#ffe55c", accent_soft="#3a3300", on_accent="#000000",
    danger="#ff8a8a", success="#6dffb0", warning="#ffd400", flag="#ff8a8a",
)

RADIUS = 7
GLASS = True  # follows ThemeManager.glass; module-level so `stylesheet(t)` keeps its signature
GLOW = "#ec4899"  # the second colour of the glass wash, opposite the accent

_extra_css: list = []


def set_brand(light: dict | None = None, dark: dict | None = None, css=None,
              high_light: dict | None = None, high_dark: dict | None = None) -> None:
    """Give the app its own colours without forking the theme: token overrides for the light and dark
    themes (`{"accent": "#0a5ad6", ...}`) and an optional `css(theme) -> str` appended to the style
    sheet for rules only this app has. Call once, before `theme.install`. A brand can't add new
    tokens; ask the kit for them."""
    global LIGHT, DARK, HIGH_LIGHT, HIGH_DARK
    LIGHT = replace(LIGHT, **(light or {}))
    DARK = replace(DARK, **(dark or {}))
    HIGH_LIGHT = replace(HIGH_LIGHT, **(high_light or {}))
    HIGH_DARK = replace(HIGH_DARK, **(high_dark or {}))
    if css is not None and css not in _extra_css:
        _extra_css.append(css)


MODES = ("system", "light", "dark")


class ThemeManager(QObject):
    """Owns the active theme; follows the system scheme unless the user picked one."""

    changed = Signal(object)  # Theme

    def __init__(self, app: QApplication):
        super().__init__(app)
        self.app = app
        self.theme = LIGHT
        mode = QSettings().value("appearance", "system")
        self.mode = mode if mode in MODES else "system"
        self.contrast = str(QSettings().value("high_contrast", "false")).lower() == "true"
        self.glass = str(QSettings().value("glass", "true")).lower() == "true"
        app.styleHints().colorSchemeChanged.connect(lambda _scheme: self.apply())
        self.apply()

    def set_contrast(self, on: bool):
        self.contrast = on
        QSettings().setValue("high_contrast", "true" if on else "false")
        self.apply()

    def set_glass(self, on: bool):
        """The frosted look: translucent surfaces over a soft colour wash. High contrast stays solid."""
        self.glass = on
        QSettings().setValue("glass", "true" if on else "false")
        self.apply()

    def set_mode(self, mode: str):
        self.mode = mode
        QSettings().setValue("appearance", mode)
        self.apply()

    def apply(self):
        if self.mode == "system":
            dark = self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        else:
            dark = self.mode == "dark"
        self.theme = (HIGH_DARK if dark else HIGH_LIGHT) if self.contrast else (DARK if dark else LIGHT)
        self.app.setPalette(palette(self.theme))
        global GLASS
        GLASS = self.glass
        self.app.setStyleSheet(stylesheet(self.theme))
        self.changed.emit(self.theme)


_manager: ThemeManager | None = None


def install(app: QApplication) -> ThemeManager:
    global _manager
    _manager = ThemeManager(app)
    return _manager


def manager() -> ThemeManager:
    assert _manager is not None, "theme.install() must run before building widgets"
    return _manager


class _Follower(QObject):
    changed = Signal(object)


_followed = None  # the theme of an app that runs its own manager (Facet), see `follow`
_follower: _Follower | None = None


def follow(t) -> None:
    """For an app with its own theme manager: tell the kit which theme is showing, so kit widgets (the
    settings switch, icons) draw in it and redraw when it changes. `t` needs the kit's colour names."""
    global _followed, _follower
    _followed = t
    if _follower is None:
        _follower = _Follower()
    _follower.changed.emit(t)


def current() -> Theme:
    if _manager is not None:
        return _manager.theme
    return _followed if _followed is not None else LIGHT


def current_color(role: str) -> QColor:
    return QColor(getattr(current(), role))


SCHOOL_LIGHT = {"bg": "#f4f6fc", "raised": "#e6ebf6", "sidebar": "#e9edf8", "accent": "#0a5ad6", "accent_hover": "#0047b3", "accent_soft": "#e2ecfd",
                "warning": "#d97706", "flag": "#b3121b"}
SCHOOL_DARK = {"bg": "#10131a", "surface": "#1a1d26", "raised": "#262b3a", "sidebar": "#151821", "accent": "#4d94ff", "accent_hover": "#6aa6ff", "accent_soft": "#15264a",
               "warning": "#f5a524", "flag": "#ff5c5c"}


def _school_css(t: Theme) -> str:
    return f"""
    #school {{ color: {t.text}; font-weight: 600; font-size: 9pt; }}
    #place {{ color: {t.muted}; font-size: 8.5pt; }}
    """


def school_brand(css=None) -> None:
    """The I.T.S. "E. Alessandrini" look (blue and red) that Gantry and Bivouac share, plus the
    `#school` / `#place` labels of the sidebar; `css(theme)` adds the app's own rules."""
    set_brand(light=SCHOOL_LIGHT, dark=SCHOOL_DARK, css=_school_css)
    if css is not None:
        set_brand(css=css)


def themed(apply) -> None:
    """Call `apply(theme)` now and again whenever the theme changes."""
    global _follower
    apply(current())

    def safe(theme):
        try:
            apply(theme)
        except RuntimeError:  # the widget was deleted
            pass
    if _manager is not None:
        _manager.changed.connect(safe)
    else:
        if _follower is None:
            _follower = _Follower()
        _follower.changed.connect(safe)


def disabled(t: Theme) -> str:
    """Text and icons of things you can't use yet: clearly paler than muted text."""
    return "#8a909c" if t.dark else "#7a808c"


def set_icon(widget, name: str, role: str = "muted", checked_role: str | None = None,
             size: int = 16) -> None:
    """Give a button a line icon that recolours with the theme."""
    def apply(t: Theme):
        widget.setIcon(icons.icon(name, getattr(t, role),
                                  getattr(t, checked_role) if checked_role else None, size,
                                  disabled(t)))
    themed(apply)


def palette(t: Theme) -> QPalette:
    p = QPalette()
    roles = {
        QPalette.Window: t.bg, QPalette.WindowText: t.text,
        QPalette.Base: t.surface, QPalette.AlternateBase: t.raised,
        QPalette.Text: t.text, QPalette.PlaceholderText: t.faint,
        QPalette.Button: t.raised, QPalette.ButtonText: t.text,
        QPalette.Highlight: t.accent, QPalette.HighlightedText: t.on_accent,
        QPalette.ToolTipBase: t.raised, QPalette.ToolTipText: t.text,
        QPalette.Link: t.accent, QPalette.Mid: t.border, QPalette.Midlight: t.hover,
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(t.faint))
    return p


def settings_css(t: Theme) -> str:
    """The Settings window (`quezka_ui.settings`): a list of sections on the left, cards of rows."""
    return f"""
    #settingsNav {{ background: {t.sidebar}; border-right: 1px solid {t.border}; }}
    QToolButton#settingsSection {{ background: transparent; border: none; border-radius: 12px;
        padding: 8px 12px; color: {t.muted}; text-align: left; font-weight: 600; }}
    QToolButton#settingsSection:hover {{ background: {t.hover}; color: {t.text}; }}
    QToolButton#settingsSection:checked {{ background: {t.accent_soft}; color: {t.text}; font-weight: 700; }}
    #settingsTitle {{ font-size: 16pt; font-weight: 800; color: {t.text}; }}
    #settingsHeading {{ font-size: 12.5pt; font-weight: 800; color: {t.text}; }}
    #rowTitle {{ color: {t.text}; font-weight: 600; }}
    #rowHint {{ color: {t.faint}; }}
    #rowLine {{ background: {t.border}; max-height: 1px; min-height: 1px; }}
    """


def material(t: Theme) -> str:
    """The Material 3 shape of things: a pill for the current page, no borders on cards, round buttons and
    soft corners, one filled colour per screen. High contrast keeps its stark lines and borders. In Qt a
    `border-radius` bigger than half the widget's height is ignored and the widget goes square, so buttons
    stop at 12 px."""
    if t in (HIGH_LIGHT, HIGH_DARK):
        return ""
    return f"""
    #sidebar {{ border-right: none; }}
    #brand {{ font-weight: 800; }}
    QToolButton#nav {{ border-radius: 16px; padding: 7px 12px; }}
    QToolButton#nav:checked {{ color: {t.text}; font-weight: 700; }}
    #card {{ border-radius: 16px; border: none; }}
    #segmented {{ border: 1px solid {t.border}; border-radius: 12px; background: transparent; }}
    QPushButton {{ border: none; border-radius: 12px; padding: 6px 14px; font-weight: 600; }}
    QToolButton {{ border: none; border-radius: 12px; }}
    QPushButton#primary {{ border-radius: 12px; font-weight: 700; padding: 6px 16px; }}
    QPushButton#segment {{ border-radius: 10px; padding: 4px 10px; }}
    QPushButton#segment:checked {{ background: {t.accent_soft}; color: {t.text}; border: none; }}
    QToolButton#icon, QPushButton#icon, QToolButton#tool {{ border-radius: 12px; }}
    QToolButton#startTile {{ border: none; border-radius: 16px; }}
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
        border-radius: 10px; }}
    QPlainTextEdit#code, QTextBrowser#code, QTextBrowser#sheetBody {{ border-radius: 12px; }}
    QTextBrowser#paper {{ border-radius: 12px; }}
    QComboBox QAbstractItemView {{ border-radius: 12px; }}
    QMenu {{ border-radius: 12px; border: 1px solid {t.border}; }}
    QMenu::item {{ border-radius: 8px; }}
    QToolTip {{ border-radius: 8px; }}
    QListWidget {{ border: none; background: transparent; }}
    QListWidget::item, QTreeWidget::item {{ border-radius: 10px; }}
    QTableView {{ border: none; border-radius: 12px; }}
    QHeaderView::section {{ border-bottom: 1px solid {t.border}; border-right: none; font-weight: 600; }}
    QCheckBox::indicator, QListWidget::indicator, QTreeWidget::indicator {{ border-radius: 5px; border-width: 2px; }}
    QScrollBar::handle {{ border-radius: 2px; }}
    QTabWidget::pane {{ border: none; }}
    QTabBar {{ qproperty-drawBase: 0; }}
    QTabBar::tab {{ background: transparent; color: {t.muted}; padding: 7px 14px; margin: 2px;
        border-radius: 12px; font-weight: 600; }}
    QTabBar::tab:hover {{ background: {t.hover}; }}
    QTabBar::tab:selected {{ background: {t.accent_soft}; color: {t.text}; }}
    QProgressBar {{ background: {t.raised}; border: none; border-radius: 4px; max-height: 8px; color: transparent; }}
    QProgressBar::chunk {{ background: {t.accent}; border-radius: 4px; }}
    QSlider::groove:horizontal {{ background: {t.raised}; height: 6px; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
    QSlider::handle:horizontal {{ background: {t.accent}; width: 16px; margin: -5px 0; border-radius: 8px; }}
    """


def _rgb(color: str) -> tuple[int, int, int]:
    c = QColor(color)
    return c.red(), c.green(), c.blue()


def mix(a: str, b: str, amount: float) -> str:
    """`a` moved `amount` (0..1) of the way towards `b`, as #rrggbb."""
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * amount) for x, y in ((ra, rb), (ga, gb), (ba, bb)))


def rgba(color: str, alpha: int) -> str:
    r, g, b = _rgb(color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def is_high_contrast(t: Theme) -> bool:
    return t in (HIGH_LIGHT, HIGH_DARK) or bool(getattr(t, "high_contrast", False))


def glass_on(t: Theme) -> bool:
    return GLASS and not is_high_contrast(t)


def wash(t: Theme) -> str:
    """The soft colour wash behind the glass: the accent from the top left, a warm glow at the bottom right."""
    a = mix(t.bg, t.accent, 0.20 if t.dark else 0.16)
    b = mix(t.bg, GLOW, 0.13 if t.dark else 0.10)
    return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {a}, stop:0.5 {t.bg}, stop:1 {b})"


def glass(t: Theme) -> str:
    """Liquid glass on top of Material 3: the window shows a colour wash and every surface is frosted,
    translucent, with a bright top edge catching the light. Text keeps the solid theme's colours, so its
    contrast doesn't change. Menus and tooltips are separate windows, which Qt can't make see-through
    everywhere: they get the glass edge on a solid surface."""
    if not glass_on(t):
        return ""
    edge = rgba("#ffffff", 34 if t.dark else 235)
    side = rgba("#ffffff", 16) if t.dark else rgba(t.accent, 40)
    pane = rgba(t.surface, 165 if t.dark else 172)
    bar = rgba(t.sidebar, 120 if t.dark else 105)
    field = rgba("#05050c", 120) if t.dark else rgba("#ffffff", 205)
    chip = rgba("#ffffff", 20) if t.dark else rgba("#ffffff", 150)
    hover = rgba("#ffffff", 34) if t.dark else rgba(t.accent, 30)
    top = mix(t.accent, "#ffffff", 0.22)
    return f"""
    QMainWindow, QDialog {{ background: {wash(t)}; }}
    #page {{ background: transparent; }}
    #sidebar {{ background: {bar}; border: none; border-right: 1px solid {side}; }}
    #card, #glass {{ background: {pane}; border: 1px solid {side}; border-top: 1px solid {edge};
        border-radius: 18px; }}
    #segmented {{ background: {chip}; border: 1px solid {side}; border-top-color: {edge}; }}
    QPushButton, QToolButton {{ background: {chip}; border: 1px solid {side}; border-top-color: {edge}; }}
    QPushButton:hover, QToolButton:hover {{ background: {hover}; }}
    QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {t.accent});
        border: 1px solid {rgba("#ffffff", 70)}; }}
    QPushButton#primary:hover {{ background: {t.accent_hover}; }}
    QToolButton#nav, QToolButton#icon, QPushButton#icon, QToolButton#tool, QPushButton#segment {{
        background: transparent; border: none; }}
    QToolButton#nav:hover, QToolButton#icon:hover, QPushButton#icon:hover, QToolButton#tool:hover {{
        background: {hover}; }}
    QToolButton#nav:checked {{ background: {rgba(t.accent, 70 if t.dark else 48)}; border: 1px solid {side};
        border-top-color: {edge}; }}
    QPushButton#segment:checked {{ background: {pane}; border: 1px solid {side}; border-top-color: {edge}; }}
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {{
        background: {field}; border: 1px solid {side}; }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
    QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 2px solid {t.accent}; }}
    QMenu, QComboBox QAbstractItemView {{ border: 1px solid {side}; border-top: 1px solid {edge}; }}
    QTableView {{ background: {pane}; alternate-background-color: {chip}; }}
    QHeaderView::section {{ background: transparent; }}
    #settingsNav {{ background: {bar}; border-right: 1px solid {side}; }}
    """


def stylesheet(t: Theme) -> str:
    check = icons.icon_file("check", t.on_accent, 3)
    chevron = icons.icon_file("chevron-down", t.muted)
    chevron_up = icons.icon_file("chevron-up", t.muted)
    r = RADIUS
    return f"""
    * {{ outline: none; }}
    QMainWindow, QDialog {{ background: {t.bg}; }}
    QToolTip {{ background: {t.raised}; color: {t.text}; border: 1px solid {t.border};
               border-radius: 5px; padding: 3px 6px; }}

    /* ---- sidebar ---- */
    #sidebar {{ background: {t.sidebar}; border-right: 1px solid {t.border}; }}
    #brand {{ font-size: 13pt; font-weight: 700; color: {t.text}; }}
    #sidebarSection {{ color: {t.faint}; font-size: 8.5pt; font-weight: 600;
                       letter-spacing: 1px; padding: 0 9px; }}
    QToolButton#nav {{ background: transparent; border: none; border-radius: 6px;
                       padding: 6px 9px; color: {t.muted}; text-align: left;
                       font-weight: 500; }}
    QToolButton#nav:hover {{ background: {t.hover}; color: {t.text}; }}
    QToolButton#nav:disabled {{ color: {disabled(t)}; background: transparent; }}
    QToolButton#nav:checked {{ background: {t.accent_soft}; color: {t.accent};
                               font-weight: 600; }}

    /* ---- page chrome ---- */
    #page {{ background: {t.bg}; }}
    #pageTitle {{ font-size: 16.5pt; font-weight: 700; color: {t.text}; }}
    #pageSubtitle {{ color: {t.muted}; }}
    #card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {r + 2}px; }}
    #cardTitle {{ font-weight: 700; color: {t.text}; font-size: 9pt; }}
    #muted {{ color: {t.muted}; }}
    #hint {{ color: {t.faint}; }}
    QLabel#danger {{ color: {t.danger}; }}
    #stat {{ font-size: 19pt; font-weight: 700; color: {t.text}; }}
    #sheetTitle {{ font-size: 14pt; font-weight: 700; color: {t.text}; }}
    QTextBrowser#sheetBody {{ background: {t.raised}; border: none; border-radius: 8px;
        padding: 8px 9px; }}
    QLabel#chip, QLabel#chipDanger {{ background: {t.raised}; color: {t.text};
        border-radius: 8px; padding: 3px 8px; font-size: 8.5pt; font-weight: 600; }}
    QLabel#chipDanger {{ background: {t.accent_soft}; color: {t.danger}; }}
    QLineEdit#titleEdit {{ font-size: 12pt; font-weight: 600; padding: 6px 8px; }}
    #tileCaption {{ color: {t.muted}; font-size: 8.5pt; font-weight: 600;
        letter-spacing: 0.5px; }}
    #tileValue {{ font-size: 17pt; font-weight: 700; color: {t.text}; }}
    #segmented {{ background: {t.raised}; border: 1px solid {t.border}; border-radius: 7px; }}
    QPushButton#segment {{ background: transparent; border: none; border-radius: 5px;
        padding: 4px 9px; color: {t.muted}; font-weight: 500; }}
    QPushButton#segment:hover {{ color: {t.text}; }}
    QPushButton#segment:checked {{ background: {t.surface}; color: {t.text};
        font-weight: 600; border: 1px solid {t.border}; }}
    #badge {{ background: {t.accent_soft}; color: {t.accent}; border-radius: 7px;
              padding: 1px 6px; font-weight: 600; font-size: 8.5pt; }}

    /* ---- buttons ---- */
    QPushButton, QToolButton {{ background: {t.raised}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 6px; padding: 5px 11px; }}
    QPushButton:hover, QToolButton:hover {{ background: {t.hover}; }}
    QPushButton:pressed, QToolButton:pressed {{ background: {t.border}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {t.faint}; background: transparent; }}
    QPushButton:checked, QToolButton:checked {{ background: {t.accent_soft}; color: {t.accent};
        border-color: {t.accent_soft}; }}
    QPushButton#primary {{ background: {t.accent}; color: {t.on_accent}; border: none;
        font-weight: 600; padding: 5px 12px; }}
    QPushButton#primary:hover {{ background: {t.accent_hover}; }}
    QPushButton#danger {{ color: {t.danger}; }}
    QToolButton#icon, QPushButton#icon {{ background: transparent; border: none;
        border-radius: 6px; padding: 5px; }}
    QToolButton#icon:hover, QPushButton#icon:hover {{ background: {t.hover}; }}
    QToolButton#icon:checked, QPushButton#icon:checked {{ background: {t.accent_soft}; }}
    QToolButton::menu-indicator, QPushButton::menu-indicator {{ image: none; width: 0; }}
    QToolButton#day {{ min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;
        padding: 0; border-radius: 10px; border: 1px solid {t.border}; background: {t.surface};
        color: {t.muted}; font-weight: 600; font-size: 8.5pt; }}
    QToolButton#day:hover {{ border-color: {t.accent}; }}
    QToolButton#day:checked {{ background: {t.accent}; border-color: {t.accent};
        color: {t.on_accent}; }}

    /* ---- the drawing page ---- */
    QToolButton#tool {{ background: transparent; border: none; border-radius: 6px;
        padding: 4px 8px; color: {t.muted}; font-weight: 500; }}
    QToolButton#tool:hover {{ background: {t.hover}; color: {t.text}; }}
    QToolButton#tool:checked {{ background: {t.accent_soft}; color: {t.accent};
        font-weight: 600; }}
    QToolButton#tool[popupMode="1"] {{ padding-right: 17px; }}
    QToolButton#tool::menu-button {{ border: none; width: 14px; }}
    QToolButton#tool::menu-arrow {{ image: url({chevron}); width: 9px; height: 9px; }}
    #rule {{ background: {t.border}; }}
    QGraphicsView {{ border: none; border-bottom-left-radius: {r + 2}px;
        border-bottom-right-radius: {r + 2}px; }}
    QPlainTextEdit#code, QTextBrowser#code {{ background: {t.raised}; border: none;
        border-radius: 8px; padding: 8px 9px; }}
    QListWidget#recent::item {{ padding: 7px 8px; }}
    QToolButton#startTile {{ background: {t.raised}; border: 1px solid {t.border};
        border-radius: 9px; padding: 11px; color: {t.text}; font-weight: 600; }}
    QToolButton#startTile:hover {{ border-color: {t.accent}; background: {t.accent_soft}; }}

    /* ---- inputs ---- */
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {{
        background: {t.surface}; color: {t.text}; border: 1px solid {t.border};
        border-radius: 6px; padding: 5px 8px; selection-background-color: {t.accent};
        selection-color: {t.on_accent}; }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus,
    QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {t.accent}; }}
    QLineEdit#search {{ background: {t.raised}; border-color: transparent; }}
    QLineEdit#search:focus {{ background: {t.surface}; border-color: {t.accent}; }}
    QTextBrowser#paper {{ background: #ffffff; color: #16181d; border: none;
        border-radius: 8px; padding: 9px 12px; }}
    QTreeWidget#compact::item {{ padding: 2px 5px; }}
    QTableView::item:selected, QTableWidget::item:selected {{ background: {t.accent_soft};
        color: {t.text}; }}
    QTableView::item:focus {{ border: 2px solid {t.accent}; }}
    QTableView::item {{ padding: 2px 6px; }}
    QTableView {{ background: {t.surface}; alternate-background-color: {t.raised};
        border: 1px solid {t.border}; border-radius: 6px; gridline-color: {t.border};
        color: {t.text}; }}
    QTableCornerButton::section {{ background: {t.raised}; border: none; }}

    QPlainTextEdit#bare, QTextBrowser#bare, QTextEdit#bare {{ border: none; background: transparent;
        padding: 3px 2px; }}
    QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 20px; }}
    QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url({chevron}); width: 11px;
        height: 11px; }}
    QTimeEdit::up-button, QTimeEdit::down-button {{ width: 0; border: none; }}
    QSpinBox, QDoubleSpinBox {{ padding-right: 19px; }}
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; width: 17px;
        border: none; background: transparent; }}
    QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-position: top right; margin-top: 3px; }}
    QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-position: bottom right; margin-bottom: 3px; }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover,
    QDoubleSpinBox::down-button:hover {{ background: {t.hover};
        border-radius: 3px; }}
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url({chevron_up}); width: 9px; height: 9px; }}
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url({chevron}); width: 9px; height: 9px; }}
    /* The list opens straight under the box, not over it with the current item aligned. */
    QComboBox {{ combobox-popup: 0; }}
    QComboBox QAbstractItemView {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: 6px; padding: 3px; selection-background-color: {t.accent_soft};
        selection-color: {t.text}; }}

    QCheckBox {{ spacing: 6px; color: {t.text}; }}
    QCheckBox::indicator, QListWidget::indicator, QTreeWidget::indicator {{
        width: 12px; height: 12px; border-radius: 4px; border: 1.5px solid {t.faint};
        background: {t.surface}; }}
    QCheckBox::indicator:hover, QListWidget::indicator:hover, QTreeWidget::indicator:hover {{
        border-color: {t.accent}; }}
    QCheckBox::indicator:checked, QListWidget::indicator:checked,
    QTreeWidget::indicator:checked {{ background: {t.accent}; border-color: {t.accent};
        image: url({check}); }}

    /* ---- lists ---- */
    QListWidget, QTreeWidget, QTableWidget {{ background: transparent; border: none;
        color: {t.text}; }}
    QListWidget::item, QTreeWidget::item {{ padding: 5px 6px; border-radius: 6px;
        margin: 1px 0; }}
    QListWidget::item:hover, QTreeWidget::item:hover {{ background: {t.hover}; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t.accent_soft};
        color: {t.text}; }}
    QTreeWidget::branch {{ background: transparent; }}
    QHeaderView::section {{ background: {t.raised}; color: {t.text}; border: none;
        border-bottom: 2px solid {t.border}; border-right: 1px solid {t.border};
        padding: 6px 8px; font-weight: 700; font-size: 9pt; }}
    QTableWidget {{ gridline-color: {t.border}; }}

    /* ---- scrollbars ---- */
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
    QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 2px; }}
    QScrollBar::handle {{ background: {t.border}; border-radius: 3px; min-height: 23px;
        min-width: 23px; }}
    QScrollBar::handle:hover {{ background: {t.faint}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

    /* ---- menus, splitters ---- */
    QMenu {{ background: {t.surface}; border: 1px solid {t.border}; padding: 5px;
        border-radius: 8px; }}
    QMenu::item {{ padding: 5px 14px 5px 9px; border-radius: 5px; color: {t.text}; }}
    QMenu::item:selected {{ background: {t.hover}; }}
    QMenu::separator {{ height: 1px; background: {t.border}; margin: 4px 6px; }}
    QSplitter::handle {{ background: transparent; }}
    QCalendarWidget QWidget {{ alternate-background-color: {t.raised}; }}
    QCalendarWidget QToolButton {{ border: none; background: transparent; }}
    """ + material(t) + settings_css(t) + glass(t) + "\n".join(rule(t) for rule in _extra_css)
