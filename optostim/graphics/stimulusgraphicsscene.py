import logging

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsItemGroup

log = logging.getLogger(__name__)


class StimulusGraphicsScene(QGraphicsScene):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._invert = False
        self.homography_transform = None
        self.setBackgroundBrush(Qt.black)

        monitor_width = 3200
        monitor_height = 1800

        self.background_image = QGraphicsRectItem(0, 0, 1, 1)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.black)
        self.background_image.setBrush(brush)
        self.addItem(self.background_image)
        self.visible_group = QGraphicsItemGroup()
        self.visible_stimuli = []

      #  self.sceneRectChanged.connect(self.on_sceneRectChanged)

        # test_rect = QGraphicsRectItem(-50, -50, 100, 100)
        # brush2 = QBrush()
        # brush2.setStyle(Qt.CrossPattern)
        # brush2.setColor(Qt.blue)
        # test_rect.setBrush(brush2)
        # self.addItem(test_rect)
        # self.test_rect = test_rect
        #test_rect.setPos(monitor_width/2, monitor_height/2)

    def display_points(self, points):
        #log.debug("Adding {} to scene.".format(points))

        for p in self.visible_stimuli:
            self.removeItem(p)

        self.visible_stimuli = []

        for p in points:
            log.debug("Adding at {} of size {}".format(p.pos(), p.rect().width()))
            self.addItem(p)
            self.visible_stimuli.append(p)

      #  self.update()

    @property
    def invert(self):
        return self._invert

    @invert.setter
    def invert(self, value):
        self._invert = value
        self.update()

    def update_background(self):
        self.background_image.setRect(self.sceneRect())
#        self.test_rect.setPos(self.sceneRect().bottomRight() / 2)

    # def on_sceneRectChanged(self, rect):
    #     log.debug("on_sceneRectChanged")
        # self.background_image.setRect(rect)


