import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget, QGraphicsView, QGraphicsScene


log = logging.getLogger(__name__)


class CameraGraphicsView(QGraphicsView):

    cursorScenePositionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewport(QOpenGLWidget())
        scene = QGraphicsScene()
        scene.setBackgroundBrush(Qt.gray)
        self.setScene(scene)
        self.setMouseTracking(True)

    # def keyPressEvent(self, event):
    #     log.debug("keyPressEvent")

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.cursorScenePositionChanged.emit(pos.x(), pos.y())
        return super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        if not self.scene().selectedItems():
            self.zoom(event)
            return
        return super().wheelEvent(event)

    def zoom(self, event):
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor
        # Save the scene pos
        oldPos = self.mapToScene(event.pos())
        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)
        # Get the new position
        newPos = self.mapToScene(event.pos())
        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())