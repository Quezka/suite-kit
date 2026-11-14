"""Design tokens, palette and style sheet. Follows the system light/dark setting."""
from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from . import icons, tokens


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
    on_accent_soft: str = "#1e1a78"  # words and icons on accent_soft (the current page, a chosen tab)
    flag: str = "#e5484d"  # a brand's signature colour, used sparingly (the school's red in Gantry)


# Material 3 flavoured: tonal surfaces tinted by the accent, with dark text, firm borders where there are
# borders, and no pale grey for anything that matters.
def _theme(name: str, dark: bool) -> "Theme":
    """A theme from the suite's tokens (tokens.py, generated from suite-rs/design/tokens.json)."""
    values = {k: v for k, v in tokens.THEMES[name].items() if k in Theme.__dataclass_fields__}
    return Theme(dark=dark, flag=values["danger"], **values)


# The suite's palette: neutral greys, one indigo accent, black and white for high contrast.
LIGHT = _theme("light", False)
DARK = _theme("dark", True)
HIGH_LIGHT = _theme("high-light", False)
HIGH_DARK = _theme("high-dark", True)

RADIUS = 7

# The shape of the Material 3 look, so every corner lines up. Outer surfaces (the sidebar, cards, the Settings
# list, the floating header) share one radius and sit one GAP from the window's edge and from each other; something
# inside one of them, touching its padding, gets the radius minus that padding, so the two curves run side by side
# (Apple's "concentric" corners).
OUTER_RADIUS = int(tokens.RADIUS['radius-lg'])
GAP = int(tokens.SPACE['gap'])
NAV_PADDING = 10  # the sidebar's inner padding
NAV_RADIUS = OUTER_RADIUS - NAV_PADDING
CARD_PADDING = int(tokens.SPACE['space-3'])  # widgets.Card's default
TILE_RADIUS = OUTER_RADIUS - CARD_PADDING
POPUP_RADIUS = int(tokens.RADIUS['radius-popup'])
POPUP_PADDING = 6

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
        app.styleHints().colorSchemeChanged.connect(lambda _scheme: self.apply())
        self.apply()

    def set_contrast(self, on: bool):
        self.contrast = on
        QSettings().setValue("high_contrast", "true" if on else "false")
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
    #school {{ color: {t.text}; font-weight: 600; font-size: {tokens.pt('caption')}pt; }}
    #place {{ color: {t.muted}; font-size: {tokens.pt('caption')}pt; }}
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
    QToolButton#settingsSection {{ background: transparent; border: none; border-radius: {NAV_RADIUS}px;
        padding: 8px 12px; color: {t.muted}; text-align: left; font-weight: 600; }}
    QToolButton#settingsSection:hover {{ background: {t.hover}; color: {t.text}; }}
    QToolButton#settingsSection:checked {{ background: {t.accent_soft}; color: {t.text}; font-weight: 700; }}
    #settingsTitle {{ font-size: {tokens.pt('headline')}pt; font-weight: 800; color: {t.text}; }}
    #settingsHeading {{ font-size: {tokens.pt('title-lg')}pt; font-weight: 800; color: {t.text}; }}
    #rowTitle {{ color: {t.text}; font-weight: 600; }}
    #rowHint {{ color: {t.faint}; }}
    #rowLine {{ background: {t.border}; max-height: 1px; min-height: 1px; }}
    """


def material(t: Theme) -> str:
    """Material 3, tonal (the suite's look since 0.13): plain tonal grounds, solid cards with big soft corners and
    no borders, a navigation rail whose current page is a tonal pill, filled inputs, round buttons with one filled
    colour per screen (`primary`). Calm on purpose: few lines, big targets, nothing that blinks or shines.
    High contrast keeps its stark lines and borders. In Qt a `border-radius` bigger than half the widget's
    height is ignored and the widget goes square, so buttons stop at 14 px."""
    if t in (HIGH_LIGHT, HIGH_DARK):
        return ""
    t = t if hasattr(t, "on_accent_soft") else replace_soft(t)
    return f"""
    #sidebar {{ background: {t.sidebar}; border: none; }}
    #brand {{ font-weight: 800; }}
    QToolButton#nav {{ border-radius: 16px; padding: 8px 12px; color: {t.muted}; font-weight: 600; }}
    QToolButton#nav[rail="true"] {{ padding: 6px 2px; font-size: {tokens.pt('caption')}pt; }}
    QToolButton#nav:hover {{ background: {t.hover}; color: {t.text}; }}
    QToolButton#nav:checked {{ background: {t.accent_soft}; color: {t.on_accent_soft}; font-weight: 700; }}
    #card {{ background: {t.surface}; border-radius: {OUTER_RADIUS}px; border: none; }}
    #segmented {{ border: 1px solid {t.border}; border-radius: 14px; background: transparent; }}
    QPushButton {{ background: {t.raised}; border: none; border-radius: 14px; padding: 8px 18px; font-weight: 600; }}
    QPushButton:hover {{ background: {t.hover}; }}
    QToolButton {{ border: none; border-radius: 14px; }}
    QPushButton#primary {{ background: {t.accent}; color: {t.on_accent}; border-radius: 14px; font-weight: 700;
        padding: 8px 20px; }}
    QPushButton#primary:hover {{ background: {t.accent_hover}; }}
    QPushButton#segment {{ border-radius: 12px; padding: 5px 12px; background: transparent; }}
    QPushButton#segment:checked {{ background: {t.accent_soft}; color: {t.on_accent_soft}; border: none; }}
    QToolButton#icon, QPushButton#icon, QToolButton#tool {{ border-radius: 14px; background: transparent; }}
    QToolButton#startTile {{ border: none; border-radius: {TILE_RADIUS}px; }}
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
        background: {t.raised}; border: 2px solid transparent; border-radius: 12px; padding: 6px 10px; }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus,
    QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{ border: 2px solid {t.accent}; }}
    QPlainTextEdit#code, QTextBrowser#code, QTextBrowser#sheetBody {{ border-radius: 12px; }}
    QPlainTextEdit#bare, QTextBrowser#bare, QTextEdit#bare {{ border: none; background: transparent; }}
    QTextBrowser#paper {{ border-radius: 12px; }}
    QComboBox QAbstractItemView {{ background: {t.surface}; border: 1px solid {t.border};
        border-radius: {POPUP_RADIUS}px; }}
    QMenu {{ background: {t.surface}; border-radius: {POPUP_RADIUS}px; border: 1px solid {t.border};
        padding: {POPUP_PADDING}px; }}
    QMenu::item {{ border-radius: {POPUP_RADIUS - POPUP_PADDING}px; padding: 8px 16px 8px 12px; }}
    QToolTip {{ background: {t.text}; color: {t.bg}; border: none; border-radius: 8px; padding: 5px 9px; }}
    QListWidget {{ border: none; background: transparent; }}
    QListWidget::item, QTreeWidget::item {{ border-radius: 12px; padding: 7px 8px; }}
    QTableView {{ border: none; border-radius: 12px; }}
    QHeaderView::section {{ border-bottom: 1px solid {t.border}; border-right: none; font-weight: 600; }}
    QCheckBox::indicator, QListWidget::indicator, QTreeWidget::indicator {{ width: 16px; height: 16px;
        border-radius: 5px; border-width: 2px; }}
    QScrollBar::handle {{ border-radius: 3px; }}
    QTabWidget::pane {{ border: none; }}
    QTabBar {{ qproperty-drawBase: 0; }}
    QTabBar::tab {{ background: transparent; color: {t.muted}; padding: 8px 16px; margin: 2px;
        border-radius: 14px; font-weight: 600; }}
    QTabBar::tab:hover {{ background: {t.hover}; }}
    QTabBar::tab:selected {{ background: {t.accent_soft}; color: {t.on_accent_soft}; }}
    QProgressBar {{ background: {t.raised}; border: none; border-radius: 4px; max-height: 8px; color: transparent; }}
    QProgressBar::chunk {{ background: {t.accent}; border-radius: 4px; }}
    QSlider::groove:horizontal {{ background: {t.raised}; height: 6px; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
    QSlider::handle:horizontal {{ background: {t.accent}; width: 18px; margin: -6px 0; border-radius: 9px; }}
    #settingsNav {{ background: {t.sidebar}; border: none; }}
    """


class _WithSoftInk:
    """An app's own theme object without `on_accent_soft` (Facet's): the words colour stands in."""

    def __init__(self, t):
        self._t = t

    def __getattr__(self, name):
        return self._t.text if name == "on_accent_soft" else getattr(self._t, name)


def replace_soft(t):
    return _WithSoftInk(t)


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
    #brand {{ font-size: {tokens.pt('title-lg')}pt; font-weight: 700; color: {t.text}; }}
    #sidebarSection {{ color: {t.faint}; font-size: {tokens.pt('caption')}pt; font-weight: 600;
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
    #pageTitle {{ font-size: {tokens.pt('headline')}pt; font-weight: 700; color: {t.text}; }}
    #pageSubtitle {{ color: {t.muted}; }}
    #card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {r + 2}px; }}
    #cardTitle {{ font-weight: 700; color: {t.text}; font-size: {tokens.pt('title')}pt; }}
    #muted {{ color: {t.muted}; }}
    #hint {{ color: {t.faint}; }}
    QLabel#danger {{ color: {t.danger}; }}
    #stat {{ font-size: {tokens.pt('display')}pt; font-weight: 700; color: {t.text}; }}
    #sheetTitle {{ font-size: {tokens.pt('title-lg')}pt; font-weight: 700; color: {t.text}; }}
    QTextBrowser#sheetBody {{ background: {t.raised}; border: none; border-radius: 8px;
        padding: 8px 9px; }}
    QLabel#chip, QLabel#chipDanger {{ background: {t.raised}; color: {t.text};
        border-radius: 8px; padding: 3px 8px; font-size: {tokens.pt('caption')}pt; font-weight: 600; }}
    QLabel#chipDanger {{ background: {t.accent_soft}; color: {t.danger}; }}
    QLineEdit#titleEdit {{ font-size: {tokens.pt('title')}pt; font-weight: 600; padding: 6px 8px; }}
    #tileCaption {{ color: {t.muted}; font-size: {tokens.pt('caption')}pt; font-weight: 600;
        letter-spacing: 0.5px; }}
    #tileValue {{ font-size: {tokens.pt('headline')}pt; font-weight: 700; color: {t.text}; }}
    #segmented {{ background: {t.raised}; border: 1px solid {t.border}; border-radius: 7px; }}
    QPushButton#segment {{ background: transparent; border: none; border-radius: 5px;
        padding: 4px 9px; color: {t.muted}; font-weight: 500; }}
    QPushButton#segment:hover {{ color: {t.text}; }}
    QPushButton#segment:checked {{ background: {t.surface}; color: {t.text};
        font-weight: 600; border: 1px solid {t.border}; }}
    #badge {{ background: {t.accent_soft}; color: {t.accent}; border-radius: 7px;
              padding: 1px 6px; font-weight: 600; font-size: {tokens.pt('caption')}pt; }}

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
        color: {t.muted}; font-weight: 600; font-size: {tokens.pt('caption')}pt; }}
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
        padding: 6px 8px; font-weight: 700; font-size: {tokens.pt('label')}pt; }}
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
    """ + material(t) + settings_css(t) + "\n".join(rule(t) for rule in _extra_css)
