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


def test_glass_is_on_by_default_and_off_in_high_contrast(app):
    m = theme.manager()
    m.set_contrast(False)
    assert m.glass
    assert "border-radius: 20px; margin: 10px 0 10px 10px" in app.styleSheet()  # the floating glass sidebar
    assert "qlineargradient(x1:0, y1:0, x2:1, y2:1" not in app.styleSheet()  # no colour wash behind anything
    m.set_contrast(True)
    assert theme.glass(m.theme) == ""
    m.set_contrast(False)
    m.set_glass(False)
    assert theme.glass(m.theme) == ""
    m.set_glass(True)


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


def test_blur_keeps_the_size_and_softens():
    from PySide6.QtGui import QImage, QColor
    from quezka_ui.glass import blur
    image = QImage(120, 60, QImage.Format_ARGB32)
    image.fill(QColor("white"))
    for x in range(0, 120, 2):
        for y in range(60):
            image.setPixelColor(x, y, QColor("black"))
    soft = blur(image)
    assert soft.size() == image.size()
    grey = soft.pixelColor(60, 30).red()
    assert 40 < grey < 215  # stripes became grey


def test_menus_become_glass_and_paint(app):
    from PySide6.QtWidgets import QMainWindow, QMenu
    from quezka_ui import glass
    glass.install(app)
    theme.manager().set_contrast(False)
    theme.manager().set_glass(True)
    w = QMainWindow()
    w.resize(300, 200)
    w.show()
    menu = QMenu(w)
    menu.addAction("One")
    menu.popup(w.mapToGlobal(w.rect().center()))
    app.processEvents()
    assert menu.property("glassy") is True
    assert not menu.grab().isNull()
    menu.close()
    w.close()


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
    assert "#card { border-radius: 20px" in sheet
    assert "QMenu::item { border-radius: 8px" in sheet  # 14 px menu, 6 px padding
    assert "22px" not in sheet and "border-radius: 16px" not in sheet


def test_see_through_only_where_the_desktop_can_blur(app, monkeypatch):
    m = theme.manager()
    m.set_contrast(False)
    monkeypatch.setattr(theme, "SEE_THROUGH_POSSIBLE", False)
    m.apply()
    assert "QMainWindow, QDialog { background: transparent" not in app.styleSheet()
    monkeypatch.setattr(theme, "SEE_THROUGH_POSSIBLE", True)
    m.set_mode("light")
    assert "QMainWindow, QDialog { background: transparent" in app.styleSheet()
    assert theme.see_through_fill(theme.current()) == "#91f3f2ff"
    m.set_see_through(False)
    assert "QMainWindow, QDialog { background: transparent" not in app.styleSheet()
    m.set_see_through(True)
    m.set_contrast(True)
    assert "QMainWindow, QDialog { background: transparent" not in app.styleSheet()  # high contrast stays solid
    m.set_contrast(False)
    monkeypatch.setattr(theme, "SEE_THROUGH_POSSIBLE", False)
    m.set_mode("system")


def test_joining_blur_my_shell_keeps_the_other_apps(monkeypatch):
    from quezka_ui import glass

    calls = []
    lists = {"whitelist": "['org.gnome.Console']"}

    def fake(*args):
        calls.append(args)
        if args[0] == "get":
            return lists.get(args[2])
        if args[0] == "set" and args[2] == "whitelist":
            lists["whitelist"] = args[3]
        return ""

    monkeypatch.setattr(glass, "_gsettings", fake)
    assert glass.join_blur_my_shell("io.github.quezka.Quire")
    assert lists["whitelist"] == "['org.gnome.Console', 'io.github.quezka.Quire']"
    assert ("set", glass.BLUR_MY_SHELL_APPS, "blur", "true") in calls
    calls.clear()
    assert glass.join_blur_my_shell("io.github.quezka.Quire")
    assert not any(c[:3] == ("set", glass.BLUR_MY_SHELL_APPS, "whitelist") for c in calls)  # already there
    lists["whitelist"] = "@as []"
    assert glass.join_blur_my_shell("x.y")
    assert lists["whitelist"] == "['x.y']"
