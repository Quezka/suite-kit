import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from quezka_ui.pages import PageStack


def test_wide_hidden_page_does_not_widen_and_callers_see_pages():
    QApplication.instance() or QApplication([])
    stack = PageStack()
    narrow, wide = QLabel("a"), QLabel("b")
    wide.setMinimumWidth(1000)
    stack.addWidget(narrow)
    stack.addWidget(wide)
    assert stack.minimumSizeHint().width() < 1000 and stack.layout().minimumSize().width() <= 480
    stack.setCurrentWidget(wide)
    assert stack.currentWidget() is wide and stack.indexOf(wide) == 1 and stack.widget(0) is narrow
