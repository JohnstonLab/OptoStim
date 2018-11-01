import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

log = logging.getLogger(__name__)


class StimulusPointPatternWidget(QWidget):

    ICON_SIZE = 16

    mouseDoubleClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # default_icon = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        # default_icon.fill(Qt.green)

        self.label = QLabel()
        #self.label.setPixmap(default_icon)

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        size_policy = self.sizePolicy()
        size_policy.setRetainSizeWhenHidden(True)
        self.setSizePolicy(size_policy)

    def mouseDoubleClickEvent(self, mouse_event):
        self.mouseDoubleClicked.emit()




