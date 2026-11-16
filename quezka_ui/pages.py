"""The main window's page stack, made to fit split screen (half of a 1366x768 laptop).

A QStackedWidget is as wide as its widest page, hidden ones too, so one wide page kept every window
~1000 px wide. Here each page sits in its own frameless scroll area: the stack asks only for the room
the current page can't do without, capped, and a page squeezed below its own minimum scrolls instead
of pushing the window wider. The scroll areas are invisible to callers: `widget`, `currentWidget`,
`indexOf` and `setCurrentWidget` all speak in pages."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QStackedWidget, QWidget

MAX_MIN_WIDTH = 480  # page area never asks more: + rail ~80-130 -> window <= fit.SPLIT_WIDTH


class _Holder(QScrollArea):
    def __init__(self, page: QWidget):
        super().__init__()
        self.page = page
        self.setObjectName("pageHolder")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # pages scroll themselves vertically -> holder only needs sideways scroll (cramped)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("QScrollArea#pageHolder, QScrollArea#pageHolder > QWidget > QWidget"
                           " { background: transparent; }")
        self.viewport().setAutoFillBackground(False)
        self.setWidget(page)

    def minimumSizeHint(self):
        hint = self.page.minimumSizeHint()
        return QSize(min(hint.width(), MAX_MIN_WIDTH), min(hint.height(), 320))

    def sizeHint(self):
        return self.page.sizeHint()


class PageStack(QStackedWidget):
    def addWidget(self, page):
        return super().addWidget(_Holder(page))

    def insertWidget(self, index, page):
        return super().insertWidget(index, _Holder(page))

    def removeWidget(self, page):
        holder = self._holder(page)
        if holder is not None:
            super().removeWidget(holder)
            page.setParent(None)

    def widget(self, index):
        holder = super().widget(index)
        return holder.page if isinstance(holder, _Holder) else holder

    def currentWidget(self):
        holder = super().currentWidget()
        return holder.page if isinstance(holder, _Holder) else holder

    def indexOf(self, page):
        holder = self._holder(page)
        return super().indexOf(holder) if holder is not None else super().indexOf(page)

    def setCurrentWidget(self, page):
        holder = self._holder(page)
        super().setCurrentWidget(holder if holder is not None else page)

    def _holder(self, page):
        for i in range(self.count()):
            holder = super().widget(i)
            if isinstance(holder, _Holder) and holder.page is page:
                return holder
        return None

    def minimumSizeHint(self):
        holder = super().currentWidget()
        return holder.minimumSizeHint() if holder is not None else QSize(0, 0)
