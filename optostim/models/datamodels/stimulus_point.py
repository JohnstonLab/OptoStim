from PyQt5.QtCore import QObject, pyqtSignal, QRectF, Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsRectItem


class StimulusPoint(QGraphicsRectItem):

    intensityChanged = pyqtSignal(float)

    def __init__(self, location=(0, 0), frame=-1, index=-1, intensity=1.0, size=1.0, parent=None):
        super().__init__(parent)
        self._intensity = intensity
        self.frame = frame
        self._location = location
        self.index = index
        self._size = size

        rect = QRectF(-size/2, -size/2, size, size)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.white)
        self.setBrush(brush)
        self.setRect(rect)
        self.setPos(location[0], location[1])

    def __repr__(self):
        return "Stimulus point at {}".format(self.pos())

    def __getstate__(self):
        return {
                'intensity': self.intensity,
                'frame': self.frame,
                'location': self.location,
                'index': self.index,
                'size': self.size
            }

    def __setstate__(self, state):
        self.intensity = state['intensity']
        self.frame = state['frame']
        self.location = state['location']
        self.index = state['index']
        self.size = state['size']
        #  todo put above within QGraphicsRectItem and update usages elsewhere

    @property
    def bottom_right(self):
        half_size = 0.5 * self.size
        return self.location[0] + half_size, self.location[1] + half_size

    @property
    def top_left(self):
        half_size = 0.5 * self.size
        return self.location[0] - half_size, self.location[1] - half_size

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, new_intensity):
        if new_intensity != self._intensity:
            self._intensity = new_intensity
            self.intensityChanged.emit(self._intensity)

    # @property
    # def frame(self):
    #     return self._frame
    #
    # @frame.setter
    # def frame(self, value):
    #     self._frame = value
    #
    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value
        self.setPos(value[0], value[1])

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, new_size):
        self._size = new_size

        rect = QRectF(-new_size/2, -new_size/2, new_size, new_size)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.white)
        self.setBrush(brush)
        self.setRect(rect)

