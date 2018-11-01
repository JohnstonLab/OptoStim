import os

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget


class CameraFrameDisplayContainer(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self._ndarray = None
        self._timer = QTimer()
        self._timer.timeout.connect(self.on_timer_timeout)
        self._timer.setSingleShot(True)

        current_directory = os.path.dirname(__file__)
        relative_location = '../../views/CameraFrameDisplayView.ui'
        path = os.path.join(current_directory, relative_location)
        uic.loadUi(path,  self)

    def adjust_camera_frame_display(self):
        new_width = self.width()
        new_height = self.height()

        if self.width() < self.height():
            new_height = self.width() * self.frameDisplayWidget.aspect_ratio
        else:
            new_width = self.height() / self.frameDisplayWidget.aspect_ratio

        self.frameDisplayWidget.resize(new_width, new_height)

    @property
    def image(self):
        return self.frameDisplayWidget.image

    @image.setter
    def image(self, new_image):
        self._ndarray = new_image
        self.frameDisplayWidget.image = new_image

    @property
    def ndarray(self):
        return self._ndarray

    def on_timer_timeout(self):
        pass

    def resizeEvent(self, event):
        self.adjust_camera_frame_display()

    def showEvent(self, event):
        self.adjust_camera_frame_display()