"""A trackpad flick keeps gliding after the fingers lift, in every scrolling widget of the app. Only a
trackpad: a mouse wheel moves in clicks and stops when you do.

While the fingers are down nothing changes, Qt scrolls as it always did. This only watches how fast that
went and, once they lift, feeds the scrollbar that was moving more of the same wheel movement, slowing
down. Going through the scrollbar's own wheel handling means lists that scroll by whole rows and pages
that scroll by pixels glide alike, at the speed the fingers left them."""
from __future__ import annotations

from math import exp
from time import monotonic

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QInputDevice, QWheelEvent
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QScrollBar

TICK_MS = 16
GLIDE_MS = 325.0  # how quickly the glide dies down: the time for the speed to fall to about a third
SAMPLE_MS = 100.0  # the speed when the fingers lift is that of this last stretch
LIFT_MS = 60  # with no end-of-gesture from the system (X11), silence this long means the fingers lifted
STILL_MS = 80.0  # fingers that rested this long before lifting meant to stop
NEW_GESTURE_MS = 200.0
START_SPEED = 0.6  # wheel units a millisecond (120 units is a click); slower than this doesn't glide
STOP_SPEED = 0.05
MAX_SPEED = 40.0
_STOPPERS = (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.TouchBegin)


def is_trackpad(event: QWheelEvent) -> bool:
    """Wayland marks a finger gesture with phases; X11 has none, but names the device a touchpad.
    (Wheel events on X11 and Windows can carry pixel deltas too, so those prove nothing.)"""
    if event.phase() != Qt.NoScrollPhase:
        return True
    device = event.device()
    return device is not None and device.type() == QInputDevice.DeviceType.TouchPad


def _scroll_areas(widget):
    while widget is not None:
        if isinstance(widget, QAbstractScrollArea):
            yield widget
        widget = widget.parentWidget()


class Glide(QObject):
    def __init__(self, parent=None, clock=monotonic):
        super().__init__(parent)
        self._clock = clock
        self._samples: list[tuple[float, int, int]] = []  # (ms, x, y)
        self._bars: list[tuple[QScrollBar, int]] = []  # every bar the gesture could move, with where it began
        self._last_seen = None
        self._last_sample = -1e9
        self._inverted = False
        self._injecting = False
        self._bar: QScrollBar | None = None
        self._horizontal = False
        self._speed = 0.0
        self._left_over = 0.0
        self._previous = 0.0
        self._lift = QTimer(self, singleShot=True, interval=LIFT_MS)
        self._lift.timeout.connect(self._lifted)
        self._timer = QTimer(self, interval=TICK_MS)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)

    def _now(self) -> float:
        return self._clock() * 1000.0

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind == QEvent.Wheel:
            if not self._injecting:
                self._wheel(obj, event)
        elif kind in _STOPPERS and self._timer.isActive():
            self.stop()
        return False

    def _wheel(self, receiver, event: QWheelEvent):
        angle = event.angleDelta()
        phase = event.phase()
        # A wheel event that nobody takes goes on to the widget's parents: the same one, seen again.
        seen = (event.timestamp(), angle.x(), angle.y(), phase)
        if seen == self._last_seen:
            return
        self._last_seen = seen
        self.stop()
        if not is_trackpad(event) or event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
            self._forget()  # a mouse, or a zoom
            return
        if phase == Qt.ScrollMomentum:  # the system glides by itself
            self._forget()
            return
        now = self._now()
        if phase == Qt.ScrollBegin or now - self._last_sample > NEW_GESTURE_MS:
            self._forget()
            self._bars = [(bar, bar.value()) for area in _scroll_areas(receiver)
                          for bar in (area.verticalScrollBar(), area.horizontalScrollBar())]
        if not angle.isNull():
            self._samples.append((now, angle.x(), angle.y()))
            self._last_sample = now
            self._inverted = event.inverted()
        if phase == Qt.ScrollEnd:
            self._lift.stop()
            self._lifted()
        elif phase == Qt.NoScrollPhase:
            self._lift.start()

    def _forget(self):
        self._samples.clear()
        self._bars.clear()
        self._lift.stop()

    def _lifted(self):
        now = self._now()
        recent = [s for s in self._samples if now - s[0] <= SAMPLE_MS]
        bars, self._bars = self._bars, []
        self._samples = []
        if len(recent) < 2 or now - recent[-1][0] > STILL_MS:
            return
        span = max(now - recent[0][0], float(TICK_MS))
        x, y = sum(s[1] for s in recent) / span, sum(s[2] for s in recent) / span
        horizontal = abs(x) > abs(y)
        speed = x if horizontal else y
        if abs(speed) < START_SPEED:
            return
        wanted = Qt.Horizontal if horizontal else Qt.Vertical
        for bar, began in bars:  # the innermost that really moved: a list at its end hands over to its page
            if bar.orientation() == wanted and bar.value() != began:
                self._bar, self._horizontal = bar, horizontal
                self._speed = max(-MAX_SPEED, min(MAX_SPEED, speed))
                self._left_over = 0.0
                self._previous = now
                self._timer.start()
                return

    def stop(self):
        self._timer.stop()
        self._bar = None

    def _tick(self):
        bar = self._bar
        try:
            alive = bar is not None and bar.isVisible()
        except RuntimeError:  # its widget was deleted
            alive = False
        if not alive:
            self.stop()
            return
        now = self._now()
        elapsed = max(1.0, now - self._previous)
        self._previous = now
        self._speed *= exp(-elapsed / GLIDE_MS)
        if abs(self._speed) < STOP_SPEED:
            self.stop()
            return
        amount = self._speed * elapsed + self._left_over
        whole = int(amount)
        self._left_over = amount - whole
        if not whole:
            return
        before = bar.value()
        self._send(bar, whole)
        if bar.value() == before and (bar.value() in (bar.minimum(), bar.maximum())):
            self.stop()  # reached the end

    def _send(self, bar: QScrollBar, amount: int):
        angle = QPoint(amount, 0) if self._horizontal else QPoint(0, amount)
        event = QWheelEvent(QPointF(1, 1), QPointF(bar.mapToGlobal(QPoint(1, 1))), QPoint(0, 0), angle,
                            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, self._inverted)
        self._injecting = True
        try:
            QApplication.sendEvent(bar, event)
        finally:
            self._injecting = False


def install(app) -> Glide:
    glide = Glide(app)
    app.installEventFilter(glide)
    app._kinetic = glide  # keep it alive
    return glide
