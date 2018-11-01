import logging
import os

import cv2
import numpy as np
from OpenGL import GL
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QObject, QEvent, Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QBrush, QPixmap, QOpenGLShaderProgram, QOpenGLShader, QMatrix4x4
from PyQt5.QtWidgets import QWidget, QGraphicsRectItem, QGraphicsScene, QOpenGLWidget, QGraphicsPixmapItem, \
    QGraphicsItem
from qimage2ndarray import gray2qimage

# from optostim.graphics.quad import GLGraphicsRectItem
from pyjohnstonlab.decorators import mock_image
from pyjohnstonlab.devices.camera_device import EXPOSURE, GAIN

log = logging.getLogger(__name__)

VERTEX = '''
    #version 330
    in vec3 vertexPosition;
    uniform mat4 projection;
    uniform mat4 view;
    uniform mat4 model;

    void main()
    {
        gl_Position = projection * view * vec4(vertexPosition, 1.0);
    }
'''

FRAGMENT = '''
    #version 330
    out vec4 colour;
    uniform bool invert;
    //uniform vec2 screen_resolution;

    void main()
    {
        colour = vec4(1.0);
        
        if (invert) 
        {
            colour = vec4(0.0, 0.0, 0.0, 1.0);
        }
    }
'''


class ClickCapture(QObject):

    def eventFilter(self, obj, event):
        #  log.debug("Event filter on {}. Type: {}".format(obj, event.type()))
        if event.type() == QEvent.GraphicsSceneMouseDoubleClick:
            #     log.debug("DoubleCLick")
            self.parent().on_frame_display_double_click(event)
        return super().eventFilter(obj, event)


class DraggableStimulusSquare(QGraphicsRectItem):

    def __init__(self, on_item_selected_has_changed_function=None, *args):
        super().__init__(*args)
        self.on_item_selected_has_changed_function = on_item_selected_has_changed_function
        self.setFlags(QGraphicsRectItem.ItemIsSelectable |
                      QGraphicsRectItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsScenePositionChanges)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange and self.scene():
            new_pos = value
            log.debug("New pos is {}".format(new_pos))
            rect = self.scene().sceneRect()
            if not rect.contains(self.rect()):
                half_width = 0.5 * self.rect().width() * self.scale()
                half_height = 0.5 * self.rect().height() * self.scale()
                new_pos.setX(min(rect.right() - half_width, max(new_pos.x(), rect.left() + half_width)))
                new_pos.setY(min(rect.bottom() - half_height, max(new_pos.y(), rect.top() + half_height)))
                return new_pos
        elif change == QGraphicsRectItem.ItemSelectedHasChanged:
            if self.on_item_selected_has_changed_function:
                self.on_item_selected_has_changed_function(value)
        return super().itemChange(change, value)

    def keyPressEvent(self, event):
        log.debug("keyPressEvent")

    def wheelEvent(self, event):
        self.zoom(event)

    def zoom(self, event):
        zoomInFactor = 1.1
        zoomOutFactor = 1 / zoomInFactor
        # Zoom
        if event.delta() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.setScale(zoomFactor * self.scale())
        event.accept()

    # def mouseMoveEvent(self, event):
    #     print("mouseMoveEvent {}, {}".format(self.pos(), self.scenePos()))
    #     super().mouseMoveEvent(event)


class OpenGLContextState:

    def __init__(self):
        self.invert = None
        self.shader_program = QOpenGLShaderProgram()
        self.vertex_attribute_object = None
        self.vertex_position = None
        self.projection = QMatrix4x4()
        self.model = QMatrix4x4()
        self.view = QMatrix4x4()


class GLDraggableStimulusSquare(DraggableStimulusSquare):

    def __init__(self, *args):
        super().__init__(*args)
        self._invert = False
        self.open_gl_contexts = {}

        width = 50
        half_width = width / 2
        x0 = -half_width
        y0 = -half_width

        self.vertex_data = np.array([
            x0, y0, 0.0,
            x0 + width, y0, 0.0,
            x0 + width, y0 + width, 0.0,

            x0 + width, y0 + width, 0.0,
            x0, y0 + width, 0.0,
            x0, y0, 0.0,
        ], dtype=np.float32)

    def initialise_gl(self):
        state = OpenGLContextState()

        state.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX)
        state.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT)

        if not state.shader_program.link():
            raise Exception("Could not link shaders - {}".format(state.shader_program.log()))

        state.vertex_attribute_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(state.vertex_attribute_object)

        vertex_buffer_object = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        state.invert = state.shader_program.uniformLocation("invert")
        state.projection = state.shader_program.uniformLocation("projection")
        state.view = state.shader_program.uniformLocation("view")
        state.model = state.shader_program.uniformLocation("model")

        state.vertex_position = state.shader_program.attributeLocation("vertexPosition")

        GL.glVertexAttribPointer(state.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        return state

    # @property
    # def invert(self):
    #     return self._invert
    #
    # @invert.setter
    # def invert(self, value):
    #     self._invert = value
    #     self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        # painter.beginNativePainting()
        #
        # if not widget.context() in self.open_gl_contexts:
        #     self.open_gl_contexts[widget.context()] = self.initialise_gl()
        #
        # context_state = self.open_gl_contexts[widget.context()]
        #
        # context_state.shader_program.bind()
        # projection = QMatrix4x4()
        # projection.ortho(painter.viewport())
        # context_state.shader_program.setUniformValue(context_state.projection, projection)
        # context_state.shader_program.setUniformValue(context_state.view, QMatrix4x4(painter.transform()))
        # context_state.shader_program.setUniformValue(context_state.invert, self.invert)
        # GL.glBindVertexArray(context_state.vertex_attribute_object)
        # GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        # GL.glBindVertexArray(0)
        # context_state.shader_program.release()
        # painter.endNativePainting()


class StimulusWindowHomographyPoint(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        width = 50
        half_width = width / 2
        self.rect = QRectF(-half_width, -half_width, width, width)
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.red)
        self.camera_square = DraggableStimulusSquare(self.on_camera_square_selected_has_changed)
        self.camera_square.setBrush(brush)
        self.camera_square.setRect(self.rect)

        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(Qt.white)

        self.stimulus_window_square = GLDraggableStimulusSquare(self.on_stimulus_window_square_selected_has_changed)
        self.stimulus_window_square.setBrush(brush)
        self.stimulus_window_square.setRect(self.rect)

    def on_stimulus_window_square_selected_has_changed(self, state):
        self.camera_square.setSelected(state)

    def on_camera_square_selected_has_changed(self, state):
        self.stimulus_window_square.setSelected(state)


class HomographyStimulusWindowWidget(QWidget):

    closed = pyqtSignal()

    def __init__(self, camera, homography_transform, stimulus_widget, parent=None):
        super().__init__(parent)
        self._camera = camera
        self._homography_transform = homography_transform
        self.homography_points = []
        self.stimulus_widget = stimulus_widget

        current_directory = os.path.dirname(__file__)
        relative_location = '../views/StimulusWindowHomographySetup.ui'
        path = os.path.join(current_directory, relative_location)
        uic.loadUi(path, self)

        self.exposureDoubleSpinBox.device = camera

        self.gainDoubleSpinBox.device = camera

        self.cameraFrameGraphicsView.setViewport(QOpenGLWidget())

        self.camera_scene = self.cameraFrameGraphicsView.scene()

        self.camera_display = QGraphicsPixmapItem()
        self.camera_scene.addItem(self.camera_display)
        self.camera_display.setPos(0, 0)
        self.camera_scene.installEventFilter(ClickCapture(self))

        self.first_shown = True

       # self.setMouseTracking(True)

       # self.stimulusWindowRepresentation.cursorScenePositionChanged.connect(self.on_stimulusWindowRepresentation_cursorScenePositionChanged)
        #self.cameraFrameGraphicsView.cursorScenePositionChanged.connect(self.on_cameraFrameGraphicsView_cursorScenePositionChanged)

    def create_points(self, x, y):
        point = StimulusWindowHomographyPoint()
        self.camera_scene.addItem(point.camera_square)
        point.camera_square.setPos(x, y)

        point.stimulus_window_square.setPos(x, y)
        self.homography_points.append(point)
        self.stimulus_widget.scene().addItem(point.stimulus_window_square)
        return point

    @pyqtSlot()
    def on_clearAllPointsButton_pressed(self):
        for point in self.homography_points:
            self.camera_scene.removeItem(point.camera_square)
            self.stimulus_widget.scene().removeItem(point.stimulus_window_square)
        self.homography_points = []

    def closeEvent(self, event):
        self._camera.newFrameReceived.disconnect(self.on_camera_newFrameReceived)
        self._camera.stop_acquisition()
        self.closed.emit()

    @property
    def frame_display(self):
        return self.cameraFrameDisplayWidget.frameDisplayWidget

  #  @mock_image('development/image-2018-01-31_15-40-12.PNG')
   # @mock_image('development/homography_fix_cam.PNG')
    @pyqtSlot(np.ndarray)
    def on_camera_newFrameReceived(self, frame):
        frame = (frame / 256.0).astype(np.uint8)  # Note this is for uint16, might have problems for other camera bits
        self.camera_display.setPixmap(QPixmap.fromImage(gray2qimage(frame)))
        self.update()

    @pyqtSlot()
    def on_calculateHomographyMatrixButton_pressed(self):
        source_centres = []
        destination_centres = []
        #  todo swap below?
        for point in self.homography_points:
            source_centres.append((point.camera_square.pos().x(), point.camera_square.pos().y()))
            destination_centres.append((point.stimulus_window_square.pos().x(), point.stimulus_window_square.pos().y()))

        log.debug("Source centres: {}".format(source_centres))
        log.debug("Destination centres: {}".format(destination_centres))

        if len(source_centres) < 3 and len(destination_centres) < 3:
            return

        # matrix, err = cv2.findHomography(np.array(source_centres),
        #                                np.array(destination_centres))
        #log.debug("Stimulus window homography matrix: {}, err: {}".format(matrix, err))
        # log.debug("Perspective matrix: {}".format(cv2.getPerspectiveTransform(np.array(destination_centres[:4]),
        #                                                                       np.array(source_centres[:4]))))
        matrix = cv2.getAffineTransform(np.array(source_centres[:3], dtype=np.float32),
                                        np.array(destination_centres[:3], dtype=np.float32))

        #log.debug("Affine matrix: {}".format())
        self._homography_transform.matrix = matrix

    @pyqtSlot(int, int)
    def on_cameraFrameGraphicsView_cursorScenePositionChanged(self, x, y):
        self.cameraWindowSceneCursorXLabel.setText("{}".format(int(x)))
        self.cameraWindowSceneCursorYLabel.setText("{}".format(int(y)))

    def on_frame_display_double_click(self, event):

        if not self.camera_display.isUnderMouse():
            return

        point = StimulusWindowHomographyPoint()
        self.camera_scene.addItem(point.camera_square)
        point.camera_square.setPos(event.scenePos().x(), event.scenePos().y())

        point.stimulus_window_square.setPos(event.scenePos().x(), event.scenePos().y())
        self.homography_points.append(point)
        self.stimulus_widget.scene().addItem(point.stimulus_window_square)

    @pyqtSlot(int, int)
    def on_stimulusWindowRepresentation_cursorScenePositionChanged(self, x, y):
        self.stimulusWindowSceneCursorXLabel.setText("{}".format(int(x)))
        self.stimulusWindowSceneCursorYLabel.setText("{}".format(int(y)))

    def showEvent(self, event):
        self._camera.newFrameReceived.connect(self.on_camera_newFrameReceived)
        self._camera.start_acquisition()
        self.stimulusWindowRepresentation.setScene(self.stimulus_widget.scene())

        if self.first_shown:
            #self.bug_fix()
            self.first_shown = False

    def bug_fix(self):
        # BUG FIX STUFF

        # [[0.00000000e+00  6.66666667e-01  6.16666667e+02]
        #  [-6.66666667e-01  0.00000000e+00  9.93333333e+02]
        # [0.00000000e+00 0.00000000e+00 1.00000000e+00]]
        # (791, 922) goes
        # to(1231.3333333333335, 466.0000000000001)
        # (1063, 365)
        # goes
        # to(860.0, 284.66666666666663)
        # (85, 320)
        # goes
        # to(830.0, 936.666666666667)
        # (696, 950)
        # goes
        # to(1250.0, 529.3333333333335)
        #
        # source = (980, 218), (980, 818), (380, 818), (380, 818), (380, 218)
        # destination = (760, 340), (1160, 340), (1160, 740), (760, 740)

        cam_width = 1360#self.camera_scene.width()
        cam_height = 1036#self.camera_scene.height()
        mid = (cam_width / 2, cam_height / 2)
        source_centres = [(mid[0] + 300, mid[1] - 300), (mid[0] + 300, mid[1] + 300), (mid[0] - 300, mid[1] + 300), (mid[0] - 300, mid[1] - 300)]

        stimulus_screen_mid = (self.stimulus_widget.width() / 2, self.stimulus_widget.height() / 2)

        destination_centres = [(stimulus_screen_mid[0] - 200, stimulus_screen_mid[1] - 200),
                       (stimulus_screen_mid[0] + 200, stimulus_screen_mid[1] - 200),
                       (stimulus_screen_mid[0] + 200, stimulus_screen_mid[1] + 200),
                       (stimulus_screen_mid[0] - 200, stimulus_screen_mid[1] + 200)]

        for i, p in enumerate(source_centres):
            stimulus_window_homography_point = self.create_points(x=p[0], y=p[1])
            stimulus_window_homography_point.stimulus_window_square.setPos(destination_centres[i][0], destination_centres[i][1])

    # self.stimulusWindowRepresentation.scene().setSceneRect(0, 0, self.stimulus_widget.width(),
#                                                               self.stimulus_widget.height())
