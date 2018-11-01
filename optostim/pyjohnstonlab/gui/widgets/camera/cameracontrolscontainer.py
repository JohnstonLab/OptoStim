from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QScrollArea, QHBoxLayout

from pyjohnstonlab.gui.widgets.camera.cameracontrolswidget import CameraControlsWidget


class CameraControlsContainer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controls_widget = CameraControlsWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self.controls_widget)
        self.scroll_area.setMaximumWidth(600)

        layout = QHBoxLayout()
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)