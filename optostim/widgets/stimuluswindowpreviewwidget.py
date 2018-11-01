from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QOpenGLWidget


class StimulusWindowPreviewWidget(QOpenGLWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self._image = QImage()

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, img):
        self._image = img.scaled(self.width(), self.height())
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)