import logging

from OpenGL import GL
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGraphicsView, QOpenGLWidget

from optostim.graphics.invertscenecoloursmixin import InvertSceneColoursMixin

log = logging.getLogger(__name__)


VERTEX = '''
    #version 330
    in vec3 vertexPosition;
    in vec2 tex_coords;
    out vec2 texture_coord;

    void main()
    {
        texture_coord = tex_coords;
        gl_Position = vec4(vertexPosition, 1.0);
    }
'''

FRAGMENT = '''
    #version 330
    in vec2 texture_coord;
    out vec4 colour;
    uniform sampler2D texture_framebuffer;

    void main()
    {
       colour = vec4(1.0) - texture(texture_framebuffer, texture_coord);
    }
'''


class StimulusWindowRepresentation(QGraphicsView, InvertSceneColoursMixin):

    cursorScenePositionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewport(QOpenGLWidget())
        self.setMouseTracking(True)

    def drawBackground(self, painter, rect):
        if not self.initialised:
            self.initialise_gl()

        if self.recreate_frame_buffer:
            self.resize_texture()

        if self.scene().invert:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frame_buffer)

        #super().drawBackground(painter, rect)
        GL.glClearColor(0.63, 0.63, 0.64, 1.0)  # RGB to match camera grey background
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    def resizeEvent(self, event):
        self.recreate_frame_buffer = True

    def drawForeground(self, painter, rect):
        if self.scene().invert:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.viewport().defaultFramebufferObject())
            self.draw_texture_to_screen()

    def keyPressEvent(self, event):
        log.debug("keyPressEvent")
        selected_items = self.scene().selectedItems()
        log.debug(selected_items)

        for item in selected_items:
            if event.key() == Qt.Key_Up:
                item.moveBy(0, -1)
            elif event.key() == Qt.Key_Down:
                item.moveBy(0, 1)
            elif event.key() == Qt.Key_Left:
                item.moveBy(-1, 0)
            elif event.key() == Qt.Key_Right:
                item.moveBy(1, 0)

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



