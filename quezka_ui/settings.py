"""The suite's Settings window and its building blocks.

Every app used to lay its settings out as one long form: labels on the left, controls and grey hints squeezed
beside them, text cut off at the right edge on a small screen. This gives them one shape instead: sections
listed on the left, each a scrolling column of cards, each card a list of rows. A row is a title, an optional
hint underneath that wraps (never clipped), and its control on the right. On/off choices are switches.

The kit holds no words of its own: apps pass their translated text.
"""
from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton, QButtonGroup, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QSizePolicy,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from . import fit, theme
from .widgets import Card, scrolling


class Switch(QAbstractButton):
    """A Material 3 switch. Same signals and methods as a checkbox (`toggled`, `isChecked`, `setChecked`)."""

    TRACK_W, TRACK_H = 46, 26

    def __init__(self, checked: bool = False, parent=None, accessible_name: str = ""):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if accessible_name:
            self.setAccessibleName(accessible_name)
        self._pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._slide)
        theme.themed(lambda _t: self.update())

    def sizeHint(self) -> QSize:
        return QSize(self.TRACK_W + 4, self.TRACK_H + 4)

    def _slide(self, on: bool):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def _get(self) -> float:
        return self._pos

    def _set(self, value: float):
        self._pos = value
        self.update()

    knob = Property(float, _get, _set)

    def paintEvent(self, _event):
        t = theme.current()
        high = theme.is_high_contrast(t)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track = QRectF(2, 2, self.TRACK_W, self.TRACK_H)
        on = self.isChecked()
        enabled = self.isEnabled()
        if on:
            p.setPen(Qt.NoPen if not high else QPen(QColor(t.text), 2))
            p.setBrush(QColor(t.accent if enabled else theme.disabled(t)))
        else:
            p.setPen(QPen(QColor(t.faint if enabled else theme.disabled(t)), 2))
            p.setBrush(QColor(t.raised))
        p.drawRoundedRect(track.adjusted(1, 1, -1, -1), self.TRACK_H / 2 - 1, self.TRACK_H / 2 - 1)
        # The knob grows when on, like Material 3's.
        size = 10 + 8 * self._pos
        x = track.left() + 5 + (self.TRACK_W - 10 - 18) * self._pos + (18 - size) / 2
        y = track.center().y() - size / 2
        p.setPen(Qt.NoPen)
        knob = QColor(t.on_accent) if on else QColor(t.faint if enabled else theme.disabled(t))
        p.setBrush(knob)
        p.drawEllipse(QRectF(x, y, size, size))
        if self.hasFocus():
            p.setPen(QPen(QColor(t.accent), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), self.height() / 2, self.height() / 2)
        p.end()

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)


class SettingsCard(Card):
    """A card of rows, separated by thin lines."""

    def __init__(self, title: str | None = None, parent=None):
        super().__init__(title, padding=16, parent=parent)
        self.body.setSpacing(10)
        self._rows = 0

    def _line(self):
        if self._rows:
            self.body.addWidget(QFrame(objectName="rowLine"))
        self._rows += 1

    def row(self, title: str, control: QWidget | None = None, hint: str | QLabel | None = None,
            stretch_control: bool = False) -> QWidget:
        """Title (and hint) on the left, the control on the right. A long control (a wide box) can stretch."""
        self._line()
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        words = QVBoxLayout()
        words.setSpacing(3)
        head = QLabel(title, objectName="rowTitle")
        head.setWordWrap(True)
        words.addWidget(head)
        if hint is not None:
            words.addWidget(self._hint(hint))
        layout.addLayout(words, 1)
        if control is not None:
            if stretch_control:
                control.setSizePolicy(QSizePolicy.Expanding, control.sizePolicy().verticalPolicy())
                control.setMinimumWidth(220)
            layout.addWidget(control, 1 if stretch_control else 0, Qt.AlignVCenter)
            if isinstance(control, Switch):
                head.setBuddy(control)
        row.title_label = head
        self.body.addWidget(row)
        return row

    def switch(self, title: str, checked: bool, hint: str | QLabel | None = None, on_toggled=None) -> Switch:
        """A row with a switch; returns the switch."""
        control = Switch(checked, accessible_name=title)
        row = self.row(title, control, hint)
        # Clicking the words flips it too, as with a checkbox.
        row.mousePressEvent = lambda _e: control.toggle() if control.isEnabled() else None
        if on_toggled is not None:
            control.toggled.connect(on_toggled)
        return control

    def wide(self, widget: QWidget | None = None, layout=None, hint: str | QLabel | None = None):
        """A full-width row: buttons, a choice of several boxes, a status line."""
        self._line()
        if widget is not None:
            self.body.addWidget(widget)
        if layout is not None:
            self.body.addLayout(layout)
        if hint is not None:
            self.body.addWidget(self._hint(hint))

    @staticmethod
    def _hint(hint) -> QLabel:
        if isinstance(hint, QLabel):
            hint.setObjectName("rowHint")
            label = hint
        else:
            label = QLabel(hint, objectName="rowHint")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label


class SettingsSection(QWidget):
    """One page of settings: a heading in a glass header (the cards scroll under it, blurred), then cards."""

    def __init__(self, title: str):
        super().__init__()
        from .glass import GlassHeader

        self.title = title
        self.column = QVBoxLayout()
        self.column.setSpacing(14)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._end = QWidget()
        self.column.addWidget(self._end, 1)
        self.area = scrolling(self.column)
        outer.addWidget(self.area)
        self.header = GlassHeader(self.area, self)
        self.header.layout.addWidget(QLabel(title, objectName="settingsHeading"))
        # `scrolling` sets its own margins on a layout; the cards start below the floating header.
        self.column.setContentsMargins(26, self.header.header_height() + 4, 26, 24)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.header.place()

    def showEvent(self, event):
        super().showEvent(event)
        self.header.place()

    def card(self, title: str | None = None) -> SettingsCard:
        card = SettingsCard(title)
        self.column.insertWidget(self.column.count() - 1, card)
        return card

    def add(self, widget: QWidget):
        self.column.insertWidget(self.column.count() - 1, widget)
        return widget


class SettingsWindow(QDialog):
    """Sections down the left (icon and name), the chosen one on the right, Close at the bottom.

    Subclass it (or build one) and call `section(name, icon)` for each page."""

    def __init__(self, title: str, close_text: str, parent=None, width: int = 900, height: int = 640):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._nav = QFrame(objectName="settingsNav")
        self._nav.setAttribute(Qt.WA_StyledBackground, True)
        self._nav_layout = QVBoxLayout(self._nav)
        self._nav_layout.setContentsMargins(12, 18, 12, 12)
        self._nav_layout.setSpacing(4)
        heading = QLabel(title, objectName="settingsTitle")
        heading.setContentsMargins(8, 0, 0, 10)
        self._nav_layout.addWidget(heading)
        self._nav_end = QWidget()
        self._nav_layout.addWidget(self._nav_end, 1)
        self.buttons = QDialogButtonBox()
        close = self.buttons.addButton(close_text, QDialogButtonBox.AcceptRole)
        close.setObjectName("primary")
        close.setCursor(Qt.PointingHandCursor)
        self.buttons.accepted.connect(self.accept)
        self._nav_layout.addWidget(self.buttons)
        self.stack = QStackedWidget()
        self._group = QButtonGroup(self)
        self._group.idClicked.connect(self.stack.setCurrentIndex)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._nav)
        root.addWidget(self.stack, 1)
        self._nav.setFixedWidth(230)
        fit.clamp_dialog(self, width, height)

    def section(self, title: str, icon: str | None = None) -> SettingsSection:
        page = SettingsSection(title)
        button = QToolButton(objectName="settingsSection", checkable=True)
        button.setText(title)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setCursor(Qt.PointingHandCursor)
        if icon:
            theme.set_icon(button, icon, "muted", "accent", size=20)
        index = self.stack.addWidget(page)
        self._group.addButton(button, index)
        self._nav_layout.insertWidget(self._nav_layout.indexOf(self._nav_end), button)
        if index == 0:
            button.setChecked(True)
        return page

    def show_section(self, index: int):
        button = self._group.button(index)
        if button is not None:
            button.setChecked(True)
            self.stack.setCurrentIndex(index)

    def sections(self) -> list[str]:
        return [self.stack.widget(i).title for i in range(self.stack.count())]


def dialog_shell(dialog: QDialog, title: str | None = None, width: int | None = None) -> None:
    dialog.setProperty("shaped", True)
    """Give an editor dialog the suite's shape after its layout is built: roomier margins, a big title on top
    and a primary Save button. Call once, before the dialog is shown."""
    layout = dialog.layout()
    if layout is None:
        return
    layout.setContentsMargins(22, 18, 22, 18)
    layout.setSpacing(max(layout.spacing(), 10))
    if title and isinstance(layout, QVBoxLayout):
        layout.insertWidget(0, QLabel(title, objectName="sheetTitle"))
    for box in dialog.findChildren(QDialogButtonBox):
        for b in box.buttons():
            b.setCursor(Qt.PointingHandCursor)
            if box.buttonRole(b) in (QDialogButtonBox.AcceptRole, QDialogButtonBox.YesRole, QDialogButtonBox.ApplyRole):
                if not b.objectName():
                    b.setObjectName("primary")
    if width:
        dialog.setMinimumWidth(width)


def shape(dialog: QDialog) -> None:
    """What every app dialog gets automatically, as it is first polished (see `fit.install`): the window
    title shown big on top, roomier margins and a primary accept button. Skipped for the Settings window,
    for dialogs that already have a title of their own, and for ones that ask with `shaped=False`."""
    if dialog.property("shaped") is not None or isinstance(dialog, SettingsWindow):
        return
    dialog.setProperty("shaped", True)
    layout = dialog.layout()
    if layout is None:
        return
    left, top, right, bottom = (layout.contentsMargins().left(), layout.contentsMargins().top(),
                                layout.contentsMargins().right(), layout.contentsMargins().bottom())
    layout.setContentsMargins(max(left, 22), max(top, 18), max(right, 22), max(bottom, 18))
    has_title = any(label.objectName() in ("sheetTitle", "settingsTitle", "pageTitle")
                    for label in dialog.findChildren(QLabel))
    title = dialog.windowTitle().strip()
    if dialog.minimumWidth() < 440 and dialog.sizeHint().width() < 440:
        dialog.setMinimumWidth(440)  # cramped forms read badly; fit.clamp_dialog still caps it on small screens
    if title and not has_title and isinstance(layout, QVBoxLayout):
        layout.insertWidget(0, QLabel(title, objectName="sheetTitle"))
    for box in dialog.findChildren(QDialogButtonBox):
        for b in box.buttons():
            b.setCursor(Qt.PointingHandCursor)
            if (box.buttonRole(b) in (QDialogButtonBox.AcceptRole, QDialogButtonBox.YesRole, QDialogButtonBox.ApplyRole)
                    and not b.objectName()):
                b.setObjectName("primary")
                b.style().unpolish(b)
                b.style().polish(b)
