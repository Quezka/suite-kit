"""The glass look, the brighter palette and the Settings window."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QComboBox

from quezka_ui import theme


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    os.environ["XDG_CONFIG_HOME"] = str(tmp_path_factory.mktemp("cfg"))
    a = QApplication.instance() or QApplication(["t"])
    a.setOrganizationName("KitTests")
    a.setApplicationName("KitTests")
    theme.install(a)
    return a


def _lum(color: str) -> float:
    c = QColor(color)
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c.red()) + 0.7152 * ch(c.green()) + 0.0722 * ch(c.blue())


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("t", [theme.LIGHT, theme.DARK])
def test_text_stays_readable_on_every_surface(t):
    # The user doesn't see well: everything that matters is at least AA (4.5:1), body text much more.
    for surface in (t.bg, t.surface, t.raised, t.sidebar, theme.mix(t.bg, t.accent, 0.2)):
        assert contrast(t.text, surface) >= 12
        assert contrast(t.muted, surface) >= 7
        assert contrast(t.faint, surface) >= 4.5
    assert contrast(t.on_accent, t.accent) >= 4.5


def test_mix_and_rgba():
    assert theme.mix("#000000", "#ffffff", 0.5) == "#808080"
    assert theme.rgba("#ff0000", 10) == "rgba(255, 0, 0, 10)"


def test_switch_behaves_like_a_checkbox(app):
    from quezka_ui.settings import Switch
    seen = []
    s = Switch(False)
    s.toggled.connect(seen.append)
    s.click()
    assert s.isChecked() and seen == [True]
    s.setChecked(False)
    assert seen == [True, False]
    s.resize(s.sizeHint())
    assert not s.grab().isNull()


def test_settings_window_sections_and_rows(app, monkeypatch):
    from PySide6.QtCore import QRect
    from quezka_ui import fit
    from quezka_ui.settings import SettingsWindow, Switch
    monkeypatch.setattr(fit, "available", lambda widget=None: QRect(0, 0, 1366, 740))
    w = SettingsWindow("Settings", "Close")
    look = w.section("Look", "palette")
    card = look.card()
    card.row("Appearance", QComboBox())
    flipped = []
    switch = card.switch("Glass", True, "Frosted surfaces", flipped.append)
    assert isinstance(switch, Switch)
    w.section("Data", "folder")
    assert w.sections() == ["Look", "Data"]
    w.show_section(1)
    assert w.stack.currentIndex() == 1
    switch.toggle()
    assert flipped == [False]
    assert w.width() <= 1366 and w.height() <= 740
    w.show()
    assert not w.grab().isNull()
    w.close()


def test_dialog_shell_marks_save_primary(app):
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout
    from quezka_ui.settings import dialog_shell
    d = QDialog()
    layout = QVBoxLayout(d)
    box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    layout.addWidget(box)
    dialog_shell(d, "New event")
    assert box.button(QDialogButtonBox.Save).objectName() == "primary"
    assert box.button(QDialogButtonBox.Cancel).objectName() != "primary"


def test_every_app_dialog_gets_its_title_and_a_primary_button(app):
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout
    from quezka_ui import fit
    fit.install(app)
    d = QDialog()
    d.setWindowTitle("New event")
    layout = QVBoxLayout(d)
    layout.addWidget(QLineEdit())
    box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    layout.addWidget(box)
    d.show()
    titles = [l.text() for l in d.findChildren(QLabel) if l.objectName() == "sheetTitle"]
    assert titles == ["New event"]
    assert box.button(QDialogButtonBox.Save).objectName() == "primary"
    assert d.minimumWidth() >= 440
    d.close()


def test_a_section_header_floats_over_its_cards(app):
    from quezka_ui.settings import SettingsWindow
    w = SettingsWindow("Settings", "Close")
    section = w.section("Look", "palette")
    for _ in range(12):
        section.card().row("A row", None)
    w.show()
    app.processEvents()
    assert section.header.isVisible() and section.header.y() == section.area.y() + theme.GAP  # inset like the cards
    first = section.column.itemAt(0).widget()
    left = first.mapTo(section, first.rect().topLeft()).x()
    assert abs(left - section.header.x()) <= 1, "the header lines up with the cards"
    assert first.mapTo(section, first.rect().topLeft()).y() >= section.header.geometry().bottom() + theme.GAP
    section.area.verticalScrollBar().setValue(80)
    app.processEvents()
    assert not section.header.grab().isNull()
    w.close()


def test_corners_nest(app):
    """Outer surfaces share one radius; what sits inside one is rounder by exactly its padding less."""
    assert theme.NAV_RADIUS == theme.OUTER_RADIUS - theme.NAV_PADDING
    assert theme.TILE_RADIUS == theme.OUTER_RADIUS - theme.CARD_PADDING
    m = theme.manager()
    m.set_contrast(False)
    sheet = app.styleSheet()
    assert f"border-radius: {theme.OUTER_RADIUS}px; border: none" in sheet and theme.OUTER_RADIUS == 28
    assert "QMenu::item { border-radius: 8px" in sheet  # 14 px menu, 6 px padding



def test_no_glass_or_see_through_left(app):
    m = theme.manager()
    m.set_contrast(False)
    sheet = app.styleSheet()
    assert "transparent; border: none; padding: 6px" not in sheet  # menus were see-through for the blur
    assert not hasattr(m, "set_glass") and not hasattr(m, "set_see_through")
    from quezka_ui import glass
    assert not hasattr(glass, "_Popups") and not hasattr(glass, "_SeeThrough")


def test_leaving_blur_my_shell_keeps_the_other_apps(monkeypatch):
    from quezka_ui import glass
    calls = []
    def fake(*args):
        calls.append(args)
        return "['org.other.App', 'io.github.quezka.Quire']" if args[0] == "get" else ""
    monkeypatch.setattr(glass, "_gsettings", fake)
    assert glass.leave_blur_my_shell("io.github.quezka.Quire")
    assert calls[-1] == ("set", glass.BLUR_MY_SHELL_APPS, "whitelist", "['org.other.App']")
