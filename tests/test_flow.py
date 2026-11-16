import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QSizePolicy, QWidget

from quezka_ui.flow import Flow


def _row(fill=True):
    QApplication.instance() or QApplication([])
    host = QWidget()
    flow = Flow(host, spacing=10, fill=fill)
    tiles = []
    for _ in range(3):
        tile = QPushButton("tile")
        tile.setMinimumSize(200, 100)
        tile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        flow.addWidget(tile, 0, len(tiles))
        tiles.append(tile)
    return host, flow, tiles


def test_narrow_wraps_and_minimum_is_one_tile():
    host, flow, tiles = _row()
    assert flow.minimumSize().width() == 200
    flow.setGeometry(host.rect().adjusted(0, 0, 0, 0).__class__(0, 0, 450, 0))
    assert tiles[0].y() == tiles[1].y() and tiles[2].y() > tiles[0].y()
    assert flow.heightForWidth(450) == 210 and flow.heightForWidth(700) == 100


def test_wide_one_line_tiles_share_width():
    host, flow, tiles = _row()
    flow.setGeometry(host.rect().__class__(0, 0, 920, 0))
    assert {t.y() for t in tiles} == {0} and {t.width() for t in tiles} == {300}


def test_buttons_keep_their_own_width_without_fill():
    host, flow, tiles = _row(fill=False)
    flow.setGeometry(host.rect().__class__(0, 0, 2000, 0))
    assert tiles[1].x() == tiles[0].width() + 10
