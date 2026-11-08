import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_every_common_widget_gets_the_compact_text_size(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from pathlib import Path

    from PySide6.QtWidgets import (QLabel, QListWidget, QMenu, QPushButton, QToolButton, QTreeWidget)

    from quezka_ui import app as kit_app

    icon = Path(kit_app.__file__).parent / "assets" / "icon.svg"
    if not icon.exists():
        icon = next(Path(kit_app.__file__).parent.rglob("*.svg"))
    app = kit_app.create_application(["t"], name="T", app_id="t.t", icon=icon, locale_package="quezka_ui")
    for cls in (QLabel, QPushButton, QToolButton, QMenu, QTreeWidget, QListWidget):
        w = cls()
        w.ensurePolished()
        assert w.font().pointSizeF() <= kit_app.BASE_PT, cls.__name__
    assert app.font().pointSizeF() <= kit_app.BASE_PT
    for cls in kit_app.THEMED_CLASSES:
        assert app.font(cls).pointSizeF() <= kit_app.BASE_PT, cls  # the per-class fonts the desktop theme would override
