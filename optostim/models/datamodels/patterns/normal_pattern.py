from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

from optostim.models.datamodels.pattern import Pattern


class NormalPattern(Pattern):
    name = "Normal"

    @classmethod
    def pixmap(cls, size=None):
        pixmap_size = size if size else cls.size
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.green)
        return pixmap