"""A row of tiles or buttons that wraps onto more lines when the window is narrow (split screen on a
1366x768 laptop), instead of forcing the window wide. Items on a line share its width when `fill`."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidgetItem


class Flow(QLayout):
    def __init__(self, parent=None, spacing: int = 10, fill: bool = True):
        super().__init__(parent)
        self._items: list = []
        self._fill = fill
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    # QLayout plumbing
    def addItem(self, item):
        self._items.append(item)

    def addWidget(self, widget, *_ignored):  # grid-style calls (row, column) keep working
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._place(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._place(rect, apply=True)

    def sizeHint(self):
        hints = [i.sizeHint() for i in self._visible()]
        if not hints:
            return QSize(0, 0)
        m = self.contentsMargins()
        width = sum(h.width() for h in hints) + self.spacing() * (len(hints) - 1)
        return QSize(width + m.left() + m.right(), max(h.height() for h in hints) + m.top() + m.bottom())

    def minimumSize(self):
        # narrowest = one item a line -> widest single item
        size = QSize()
        for item in self._visible():
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _visible(self):
        return [i for i in self._items if not (i.widget() and i.widget().isHidden())]

    def _lines(self, width):
        lines, line, used = [], [], 0
        for item in self._visible():
            w = item.minimumSize().width() if self._fill else min(item.sizeHint().width(), width)
            extra = w + (self.spacing() if line else 0)
            if line and used + extra > width:
                lines.append(line)
                line, used = [], 0
                extra = w
            line.append((item, w))
            used += extra
        if line:
            lines.append(line)
        return lines

    def _place(self, rect, apply):
        m = self.contentsMargins()
        inner = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        y = inner.y()
        lines = self._lines(inner.width())
        for n, line in enumerate(lines):
            height = max(item.sizeHint().height() if item.sizeHint().height() > 0 else item.minimumSize().height()
                         for item, _w in line)
            if apply:
                x = inner.x()
                if self._fill:
                    # same width each on a line = width of a full line's share <- tiles line up across lines
                    per = max(len(lines[0]), 1)
                    share = (inner.width() - self.spacing() * (per - 1)) // per
                for item, w in line:
                    if self._fill:
                        expand = item.expandingDirections() & Qt.Horizontal or (
                            item.widget() and item.widget().sizePolicy().horizontalPolicy() & QSizePolicy.ExpandFlag)
                        w = max(w, share) if expand else w
                    item.setGeometry(QRect(QPoint(x, y), QSize(w, height)))
                    x += w + self.spacing()
            y += height + (self.spacing() if n < len(lines) - 1 else 0)
        return y - inner.y() + m.top() + m.bottom()
