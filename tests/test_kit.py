import pytest

from PySide6.QtWidgets import QApplication

from quezka_ui import app as kit_app
from quezka_ui import i18n, icons, theme
from quezka_ui.widgets import Card, Page, Segmented, scrolling

LOCALES = "tests.fake_locales"


@pytest.fixture(scope="module")
def qt():
    application = kit_app.create_application(["kit"], name="KitTest", app_id="io.github.quezka.KitTest",
                                             icon=icons.APP_ICON, locale_package=LOCALES)
    i18n.install("en", application)
    return application


def test_the_kit_carries_every_apps_icons_and_apps_can_add_their_own():
    for name in ("plus", "moon", "drop", "align", "gantt", "database", "link", "arrow-up-right"):
        assert name in icons.names()
    assert icons.svg("link", "#000") != icons.svg("arrow-up-right", "#000")  # the chain and the arrow
    assert icons.svg("home", "#000", filled=True) != icons.svg("home", "#000")  # selected is filled
    assert icons.svg("bold", "#000", filled=True) == icons.svg("bold", "#000")  # nothing to fill: stays as it is
    assert 'stroke="#000"' in icons.svg("entity", "#000")  # a notation stays a line drawing
    icons.register({"kit-test-icon": "<circle cx='12' cy='12' r='4'/>"})
    icons.register({"kit-test-icon": "<circle cx='12' cy='12' r='4'/>"})  # again, the same: fine
    with pytest.raises(ValueError):
        icons.register({"entity": "<path d='M0 0'/>"})  # a name can't change its drawing
    plus = icons.svg("plus", "#000")
    icons.register({"plus": "<path d='M0 0'/>"})  # and one with a Material symbol keeps the symbol
    assert icons.svg("plus", "#000") == plus
    assert "currentColor" not in icons.svg("plus", "#123456") and "#123456" in icons.svg("plus", "#123456")


def test_catalogues_come_from_the_apps_package_and_text_falls_back_to_english(qt):
    assert i18n.install("it", qt) == "it"
    assert i18n._("Hello") == "Ciao" and i18n._("Unknown") == "Unknown"
    assert i18n.C_("button", "Hello") == "Ciao"
    assert i18n.plural(2, "entity") == "2 entità"
    i18n.install("ru", qt)
    assert i18n.plural(5, "entity") == "5 сущностей" and i18n.plural(2, "entity") == "2 сущности"
    i18n.install("en", qt)
    assert i18n._("Hello") == "Hello"


def test_plural_accepts_a_whole_word_or_an_ending_like_the_apps_always_did(qt):
    i18n.install("en", qt)
    assert i18n.plural(1, "class", "es") == "1 class" and i18n.plural(3, "class", "es") == "3 classes"
    assert i18n.plural(3, "entity", "entities") == "3 entities"
    assert i18n.plural(2, "event") == "2 events" and i18n.plural(0, "event") == "0 events"


def test_light_and_dark_themes_have_the_same_tokens_and_switch(qt):
    manager = theme.manager()
    for mode in ("light", "dark", "system"):
        manager.set_mode(mode)
        assert theme.current().accent
    assert theme.LIGHT.accent != theme.DARK.accent
    assert theme.LIGHT.__dict__.keys() == theme.DARK.__dict__.keys()
    assert theme.disabled(theme.LIGHT) != theme.disabled(theme.DARK)


def test_page_card_segmented_and_scrolling_build(qt):
    page = Page(margins=(10, 10, 10, 10), spacing=4)
    page.title.setText("T")
    page.leading.addWidget(Segmented([("a", "A"), ("b", "B")]))
    card = Card("Title")
    page.root.addWidget(scrolling(card.body_layout if hasattr(card, "body_layout") else card.body))
    page.show()
    qt.processEvents()
    assert page.minimumSizeHint().height() < 400 and not page.grab().isNull()
    page.close()


def test_create_application_sets_the_apps_identity(qt):
    assert QApplication.applicationName() == "KitTest"
    assert QApplication.desktopFileName() == "io.github.quezka.KitTest"
    assert not QApplication.windowIcon().isNull()


def test_a_brand_changes_colours_and_adds_rules_without_forking_the_theme(qt):
    from dataclasses import replace
    original = (theme.LIGHT, theme.DARK, list(theme._extra_css))
    try:
        theme.set_brand(light={"accent": "#0a5ad6", "flag": "#b3121b"}, dark={"accent": "#4d94ff"},
                        css=lambda t: f"#school {{ color: {t.text}; }}")
        assert theme.LIGHT.accent == "#0a5ad6" and theme.DARK.accent == "#4d94ff"
        assert theme.LIGHT.text == original[0].text  # everything else stays the suite's
        assert "#school" in theme.stylesheet(theme.LIGHT) and "#0a5ad6" in theme.stylesheet(theme.LIGHT)
        theme.set_brand(css=theme._extra_css[-1])  # the same rule twice is added once
        assert len(theme._extra_css) == len(original[2]) + 1
    finally:
        theme.LIGHT, theme.DARK = original[0], original[1]
        theme._extra_css[:] = original[2]
    assert "#school" not in theme.stylesheet(theme.LIGHT)


def test_logo_tile_draws_on_a_white_rounded_tile(qt):
    from quezka_ui.widgets import logo_tile
    tile = logo_tile(str(icons.APP_ICON), str(icons.APP_ICON), 48, 2.0)
    assert tile.width() == 96 and tile.devicePixelRatio() == 2.0 and not tile.isNull()


def test_high_contrast_is_a_mode_of_the_theme_and_is_remembered(qt):
    manager = theme.manager()
    manager.set_mode("light")
    manager.set_contrast(False)
    normal = theme.current()
    manager.set_contrast(True)
    high = theme.current()
    assert high is theme.HIGH_LIGHT and high.text == "#000000" and high.border == "#000000"
    manager.set_mode("dark")
    assert theme.current() is theme.HIGH_DARK
    manager.set_contrast(False)
    assert theme.current() is theme.DARK and theme.current() != normal
    from PySide6.QtCore import QSettings
    assert str(QSettings().value("high_contrast")).lower() == "false"


def test_the_comfortable_palette_keeps_text_dark_and_borders_firm():
    def luminance(hex_):
        r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    assert luminance(theme.LIGHT.text) < 0.1 and luminance(theme.LIGHT.muted) < 0.35  # nothing pale that matters
    assert abs(luminance(theme.LIGHT.border) - luminance(theme.LIGHT.surface)) > 0.2  # borders you can see
    assert {"book-open", "cube", "ruler"} <= icons.names()


def test_the_school_brand_is_shared_and_apps_can_add_rules(qt):
    original = (theme.LIGHT, theme.DARK, list(theme._extra_css))
    try:
        theme.school_brand(css=lambda t: "#only-here { color: red; }")
        assert theme.LIGHT.accent == "#0a5ad6" and theme.DARK.accent == "#4d94ff" and theme.LIGHT.flag == "#b3121b"
        sheet = theme.stylesheet(theme.LIGHT)
        assert "#school" in sheet and "#place" in sheet and "#only-here" in sheet
    finally:
        theme.LIGHT, theme.DARK = original[0], original[1]
        theme._extra_css[:] = original[2]


def test_a_button_menu_opens_exactly_under_the_button_or_above_when_there_is_no_room():
    from PySide6.QtCore import QRect
    from quezka_ui.fit import MENU_GAP, menu_position
    area = QRect(0, 0, 1366, 768)
    assert menu_position(100, 40, 70, 200, 300, area).toTuple() == (100, 70 + MENU_GAP)
    assert menu_position(100, 700, 730, 200, 300, area).toTuple() == (100, 700 - MENU_GAP - 300)  # at the bottom
    assert menu_position(1300, 40, 70, 200, 300, area).toTuple() == (1166, 70 + MENU_GAP)  # stays on the screen
    assert menu_position(0, 300, 330, 200, 700, area).y() == 68  # too tall either way: still on the screen


def test_the_aligner_moves_a_real_menu_when_it_shows():
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication, QMenu, QPushButton
    from quezka_ui import fit
    app = QApplication.instance() or QApplication([])
    fit.install(app)
    button = QPushButton("Add")
    menu = QMenu(button)
    menu.addAction("One")
    button.setMenu(menu)
    button.resize(80, 30)
    button.move(40, 20)
    button.show()
    app.processEvents()
    menu.popup(QPoint(500, 500))  # wherever Qt or a style would have put it
    app.processEvents()
    corner = button.mapToGlobal(QPoint(0, 0))
    area = button.screen().availableGeometry()
    assert menu.pos() == fit.menu_position(corner.x(), corner.y(), corner.y() + button.height(),
                                           menu.sizeHint().width(), menu.sizeHint().height(), area)
    menu.close()
    button.close()
