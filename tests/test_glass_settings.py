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
    assert "qlineargradient" in app.styleSheet()
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
