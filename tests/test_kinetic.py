import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo, QWheelEvent
from PySide6.QtWidgets import QApplication, QListWidget, QScrollArea, QWidget

from quezka_ui import fonts, kinetic


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class Clock:
    now = 100.0

    def __call__(self):
        return self.now


def wheel(y, phase, x=0, modifiers=Qt.NoModifier, ts=None):
    return QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(x, y), Qt.NoButton, modifiers, phase, False)


@pytest.fixture
def scene(app):
    area = QScrollArea()
    content = QWidget()
    content.setMinimumSize(200, 20000)
    area.setWidget(content)
    area.resize(200, 200)
    area.show()
    clock = Clock()
    glide = kinetic.Glide(clock=clock)
    app.processEvents()
    yield area, glide, clock
    glide.stop()
    area.close()


def flick(area, glide, clock, phase_end=True, speed=120, gap=0.016):
    """Fingers moving at `speed` wheel units each `gap` seconds, then lifting."""
    viewport = area.viewport()
    glide._wheel(viewport, wheel(0, Qt.ScrollBegin))
    for i in range(6):
        clock.now += gap
        event = wheel(-speed, Qt.ScrollUpdate)
        event.setTimestamp(i + 1)
        glide._wheel(viewport, event)
        QApplication.sendEvent(area.verticalScrollBar(), wheel(-speed, Qt.NoScrollPhase))
    if phase_end:
        clock.now += gap
        event = wheel(0, Qt.ScrollEnd)
        event.setTimestamp(100)
        glide._wheel(viewport, event)


def run_out(glide, clock, ticks=400):
    for _ in range(ticks):
        if not glide._timer.isActive():
            break
        clock.now += 0.016
        glide._tick()


def test_a_flick_keeps_going_then_stops_by_itself(scene):
    area, glide, clock = scene
    flick(area, glide, clock)
    bar = area.verticalScrollBar()
    lifted_at = bar.value()
    assert lifted_at > 0 and glide._timer.isActive()
    clock.now += 0.016
    glide._tick()
    first = bar.value() - lifted_at
    run_out(glide, clock)
    assert bar.value() > lifted_at + first and not glide._timer.isActive()


def test_a_mouse_wheel_never_glides(scene):
    area, glide, clock = scene
    for i in range(6):
        clock.now += 0.016
        event = wheel(-120, Qt.NoScrollPhase)
        event.setTimestamp(i + 1)
        glide._wheel(area.viewport(), event)
        QApplication.sendEvent(area.verticalScrollBar(), wheel(-120, Qt.NoScrollPhase))
    glide._lifted()
    assert not glide._timer.isActive()
    assert not kinetic.is_trackpad(wheel(-120, Qt.NoScrollPhase))
    assert kinetic.is_trackpad(wheel(-12, Qt.ScrollUpdate))


def test_resting_before_lifting_means_stop(scene):
    area, glide, clock = scene
    flick(area, glide, clock, phase_end=False)
    clock.now += 0.2
    event = wheel(0, Qt.ScrollEnd)
    event.setTimestamp(100)
    glide._wheel(area.viewport(), event)
    assert not glide._timer.isActive()


def test_a_slow_drag_does_not_glide(scene):
    area, glide, clock = scene
    flick(area, glide, clock, speed=2)
    assert not glide._timer.isActive()


def test_nothing_moved_nothing_glides(app):
    """A gesture over something that took it itself (a spin box, a canvas that zooms) leaves the page be."""
    area = QScrollArea()
    content = QWidget()
    content.setMinimumSize(200, 20000)
    area.setWidget(content)
    clock = Clock()
    glide = kinetic.Glide(clock=clock)
    glide._wheel(area.viewport(), wheel(0, Qt.ScrollBegin))
    for i in range(6):
        clock.now += 0.016
        event = wheel(-120, Qt.ScrollUpdate)
        event.setTimestamp(i + 1)
        glide._wheel(area.viewport(), event)
    glide._lifted()
    assert not glide._timer.isActive()


def test_a_click_or_new_gesture_stops_the_glide_and_the_end_stops_it_too(scene):
    area, glide, clock = scene
    flick(area, glide, clock)
    assert glide._timer.isActive()
    glide.eventFilter(area, QEvent(QEvent.MouseButtonPress))
    assert not glide._timer.isActive()
    flick(area, glide, clock)
    bar = area.verticalScrollBar()
    bar.setValue(bar.maximum())
    clock.now += 0.016
    glide._tick()
    assert not glide._timer.isActive()


def test_a_list_that_scrolls_by_rows_glides_too(app):
    rows = QListWidget()
    rows.addItems([str(i) for i in range(2000)])
    rows.setVerticalScrollMode(QListWidget.ScrollPerItem)
    rows.resize(200, 200)
    rows.show()
    app.processEvents()
    clock = Clock()
    glide = kinetic.Glide(clock=clock)
    flick(rows, glide, clock)
    lifted_at = rows.verticalScrollBar().value()
    run_out(glide, clock)
    assert rows.verticalScrollBar().value() > lifted_at
    rows.close()


def test_the_typeface_loads_with_its_weights_and_cyrillic(app):
    assert fonts.load() == "Manrope"
    assert "Manrope" in QFontDatabase.families()
    regular = QFont("Manrope", 12)
    assert QFontInfo(regular).family() == "Manrope"
    from PySide6.QtGui import QFontMetricsF
    widths = {w: QFontMetricsF(QFont("Manrope", 40, w)).horizontalAdvance("Manrope Жизнь") for w in (400, 500, 600, 700)}
    assert widths[400] < widths[500] < widths[600] < widths[700]  # each is really its own weight
    assert QFontDatabase.WritingSystem.Cyrillic in QFontDatabase.writingSystems("Manrope")
