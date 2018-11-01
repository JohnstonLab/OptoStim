import logging

import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QOpenGLWidget

log = logging.getLogger(__name__)


class CameraFrameDisplayWidget(QOpenGLWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self._frame_count = 0
        self._timer = QTimer()
        self._previous_time = 0
        self._timer.timeout.connect(self.on_timer_timeout)
        self._timer.setSingleShot(True)

    @property
    def aspect_ratio(self):
        if self._image.width() == 0:
            return 1.0
        else:
            return self._image.height() / self._image.width()

    def paintEvent(self, paint_event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image):
        height, width = new_image.shape
        # Note this is for uint16, might have problems for other camera bits
        img_8bit = (new_image / 256.0).astype(np.uint8) if not new_image.dtype == np.uint8 else new_image
        self._image = QImage(img_8bit.data, width, height, QImage.Format_Grayscale8)
        self.update()

    def on_timer_timeout(self):
        min_width = int(self.height() * self.aspect_ratio)
        self.setMinimumWidth(min_width)

    # def resizeEvent(self, event):
    #     self._timer.start(500)

    def set_image(self, new_image):
        self.image = new_image
