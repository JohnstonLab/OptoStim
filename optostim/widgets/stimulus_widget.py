import ctypes
import logging

import cv2
import numpy as np
# OpenGL.FULL_LOGGING = True
import qimage2ndarray
from OpenGL import GL
from PyQt5.QtCore import pyqtSignal, QPointF, Qt
from PyQt5.QtGui import QPen, QTransform, QResizeEvent, QOpenGLShader, QMatrix4x4, QOpenGLShaderProgram, \
    QVector3D, QVector2D, QBrush
from PyQt5.QtWidgets import QApplication, QOpenGLWidget, QGraphicsView, QGraphicsLineItem

from optostim.graphics.crosshair import Crosshair
from optostim.graphics.gaussianintensitymaskrenderer import GaussianIntensityMaskRenderer
from optostim.graphics.invertscenecoloursmixin import InvertSceneColoursMixin
from pyjohnstonlab.curves import Gaussian

log = logging.getLogger(__name__)

VERTEX = """#version 330
        layout(location=0) in vec3 vertexPosition;
        layout(location=1) in vec2 vertexTexCoords;
       // uniform mat3 homography_matrix;
        //uniform mat4 transformationMatrix;
        uniform mat4 projection_matrix;
        uniform mat4 view_matrix;
        out vec2 textureCoords;

        void main() {
           gl_Position = projection_matrix * view_matrix * vec4(vertexPosition, 1.0);
            textureCoords = vertexTexCoords;
        }"""

FRAGMENT = """#version 330
        in vec2 textureCoords;
        uniform sampler2D textureSampler;
        uniform bool inverted;
        out vec4 colour;

/*

        uniform bool intensity_mask;
        uniform mat3 homography_matrix;
        uniform mat4 projection_matrix;
        uniform mat4 view_matrix;

        uniform float centre_x;
        uniform float centre_y;        
        uniform float height;
        uniform float rotation;
        uniform float max_height;
        uniform vec2 shape;
        uniform float width_x;
        uniform float width_y;
        
        float gaussianMask(float x, float y)
        {
            float rotation_radians = radians(rotation);
            
            float centre_x2 = centre_x * cos(rotation_radians) - centre_y * sin(rotation_radians);
            float centre_y2 = centre_x * sin(rotation_radians) + centre_y * cos(rotation_radians);
            
            float xp = x * cos(rotation_radians) - y * sin(rotation_radians);
            float yp = x * sin(rotation_radians) + y * cos(rotation_radians);
            
           float a = pow((centre_x2 - xp) / width_x, 2);
           float b = pow((centre_y2 - yp) / width_y, 2);
            
            float gaussian = height * exp(-0.5 * (a + b));
            
            return (1.0 - gaussian / height);
        }*/
        
        void main() {
              colour = texture(textureSampler, textureCoords);
              
             /* if (intensity_mask)
              {
              vec3 transformed = homography_matrix * vec3(textureCoords.x, textureCoords.y, 1.0);
              
                  float y = transformed.x;// * shape.y;
                  float x = (1 - transformed.y);// * shape.x;
                  
                    colour.xyz = vec3(gaussianMask(x,  y));
                     // colour = colour * gaussianMask();
               }*/
              
           if (inverted)
           {
                colour = vec4(1.0 - colour.r, 1.0 - colour.g, 1.0 - colour.b, 1.0);
            }
        }"""


class StimulusWidget(QOpenGLWidget):

    shown = pyqtSignal()
    closed = pyqtSignal()
    backgroundColourChanged = pyqtSignal(float)
    invertedChanged = pyqtSignal(bool)
    resized = pyqtSignal(QResizeEvent)

    def __init__(self, homography_transform, parent=None):
        super().__init__(parent)
        self._background_colour = None
        self._drawables = []
        self._image = None
        self._intensity_mask = None
        self.centre_x_uniform = None
        self.centre_y_uniform = None
        self.crosshair = Crosshair(self)
        self.height_uniform = None
        self.image_to_upload = None
        self.gl_initialised = False
        self.shape_uniform = None
        self.max_height_uniform = None
        self.rotation_uniform = None
        self.texture = -1
        self.texture_uploaded = False
        self.width_x_uniform = None
        self.width_y_uniform = None
        self.homography_transform = homography_transform
        self.projection_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self.set_background_colour(0)
        self.shader_program = QOpenGLShaderProgram()
        self._show_crosshair = False
        self._show_scale_bar = False
        self._crosshair_thickness = 1
        self._gaussian_shape = QVector2D()
        self._image_to_render = None
        self._inverted = False
        self._scale_bar_thickness = 1
        self._scale_bar_width = 10
        self._use_homography = False
        self._use_intensity_mask = False

        self.gaussian = Gaussian()

        self.transform = QTransform()
        self.dx = 0
        self.dy = 0
        self.rotation = 0
        self.scale_value = 1

        self.setWindowTitle('Stimulus Window')

        self.homography_transform.matrixChanged.connect(self.update_image)

    def compute_transformation_matrix(self):
        self.view_matrix.setToIdentity()

        dx = self.dx / (0.5 * self.width())
        dy = -self.dy / (0.5 * self.height())

        self.view_matrix.scale(self.scale)
        self.view_matrix.rotate(self.rotation, QVector3D(0, 0, 1))
        self.view_matrix.translate(dx, dy, 0)

    def full_brightness(self):
        return 255.0 if self.inverted else 0.0

    @property
    def background_colour(self):
        return self._background_colour

    @background_colour.setter
    def background_colour(self, new_background):
        new_background = int(new_background)
        self.set_background_colour(new_background)

    def closeEvent(self, event):
        self.closed.emit()

    @property
    def crosshair_thickness(self):
        return self._crosshair_thickness

    @crosshair_thickness.setter
    def crosshair_thickness(self, thickness):
        self._crosshair_thickness = thickness
        self.update()

    @property
    def drawables(self):
        return self._drawables

    @drawables.setter
    def drawables(self, new_drawables):
        self._drawables = new_drawables
        self.gl_initialised = False
        self.update()

    def upload_texture(self):
        self.create_texture(self.image_to_upload)
        self.texture_uploaded = True

    def create_texture(self, image):
        log.info("Creating texture")
        img_data = np.flipud(image)
        height, width = img_data.shape

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)

        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, width, height, 0,
                        GL.GL_LUMINANCE, GL.GL_UNSIGNED_BYTE, img_data)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    @property
    def homography(self):
        return self._homography

    @homography.setter
    def homography(self, value):
        self._homography = value
        self.update()

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, img):
        self._image = img
        if self._image is not None:
            self.update_image()
        self.update()

    def initializeGL(self):
        log.info("OpenGL Vendor: {}".format(GL.glGetString(GL.GL_VENDOR)))
        log.info("OpenGL Renderer: {}".format(GL.glGetString(GL.GL_RENDERER)))
        log.info("OpenGL Version: {}".format(GL.glGetString(GL.GL_VERSION)))

        for drawable in self.drawables:
            drawable.initialise_gl()

        return

        self.texture = GL.glGenTextures(1)

        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX)
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT)

        if not self.shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.shader_program.log()))

        LOC = 1.0

        vertexData = np.array([
            # X,    Y,   Z     U,   V
            -LOC, LOC, 0.0, 0.0, 1.0,
            LOC, LOC, 0.0, 1.0, 1.0,
            LOC, -LOC, 0.0, 1.0, 0.0,

            LOC, -LOC, 0.0, 1.0, 0.0,
            -LOC, -LOC, 0.0, 0.0, 0.0,
            -LOC, LOC, 0.0, 0.0, 1.0,
        ], dtype=np.float32)

        self.VAO = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.VAO)

        VBO = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, VBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertexData.nbytes, vertexData,
                        GL.GL_STATIC_DRAW)

        vertex_position = self.shader_program.attributeLocation("vertexPosition")

        self.homography_matrix_uniform = self.shader_program.uniformLocation("homography_matrix")
        self.intensity_mask_uniform = self.shader_program.uniformLocation("intensity_mask")
        self.inverted_uniform = self.shader_program.uniformLocation("inverted")
        self.projection_matrix_uniform = self.shader_program.uniformLocation("projection_matrix")
        self.view_matrix_uniform = self.shader_program.uniformLocation("view_matrix")

        self.centre_x_uniform = self.shader_program.uniformLocation("centre_x")
        self.centre_y_uniform = self.shader_program.uniformLocation("centre_y")
        self.height_uniform = self.shader_program.uniformLocation("height")
        self.shape_uniform = self.shader_program.uniformLocation("shape")
        self.width_x_uniform = self.shader_program.uniformLocation("width_x")
        self.width_y_uniform = self.shader_program.uniformLocation("width_y")
        self.rotation_uniform = self.shader_program.uniformLocation("rotation")

        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 20,
                                 None)

        GL.glVertexAttribPointer(texture_coords, 2, GL.GL_FLOAT, GL.GL_TRUE, 20,
                                 ctypes.c_void_p(12))

        self.texture_sampler = self.shader_program.uniformLocation("textureSampler")

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        self.crosshair.initialise_gl()

        self.gl_initialised = True

    @property
    def intensity_mask(self):
        return self._intensity_mask

    @intensity_mask.setter
    def intensity_mask(self, new_mask):
        self._intensity_mask = new_mask

    @property
    def inverted(self):
        return self._inverted

    @inverted.setter
    def inverted(self, invert):
        if invert != self._inverted:
            self._inverted = invert
            self.background_colour = ~self._background_colour & 0xFF
            self.invertedChanged.emit(self._inverted)
            self.update()

    def open(self):

        desktop = QApplication.desktop()
        is_fullscreen = desktop.screenCount() > 1

        if is_fullscreen:
            screen_widget_on = desktop.screenNumber(QApplication.activeWindow())
            next_screen_not_in_use = (screen_widget_on + 1) % desktop.screenCount()
            other_screen_geometry = desktop.screenGeometry(next_screen_not_in_use)
            self.move(other_screen_geometry.x(), other_screen_geometry.y())
            self.showFullScreen()
        else:
            self.resize(1024, 1024)
            self.show()

        self.showFullScreen() if is_fullscreen else self.show()

    def paint_gl_image(self):

        if not self.texture_uploaded:
            self.upload_texture()

        log.debug("paint gl image: texture: {}, sampler: {}".format(self.texture, self.texture_sampler))
        self.shader_program.bind()

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glUniform1i(self.texture_sampler, 0)

    #    homography = self.homography_matrix if self.use_homography else np.identity(3, dtype=np.float32)
        #mat = QMatrix3x3()
        #self.shader_program.setUniformValue(self.homography_matrix_uniform, mat)
     #   GL.glUniformMatrix3fv(self.homography_matrix_uniform, 1, GL.GL_FALSE, homography)
       # self.shader_program.setUniformValue(self.homography_matrix_uniform, homography)

        self.shader_program.setUniformValue(self.inverted_uniform, self.inverted)
     #   self.shader_program.setUniformValue(self.intensity_mask_uniform, self._intensity_mask)
        self.shader_program.setUniformValue(self.projection_matrix_uniform, self.projection_matrix)
        self.shader_program.setUniformValue(self.view_matrix_uniform, self.view_matrix)

        # self.shader_program.setUniformValue(self.height_uniform, self.gaussian.amplitude)
        # self.shader_program.setUniformValue(self.centre_x_uniform, self.gaussian.x0)
        # self.shader_program.setUniformValue(self.centre_y_uniform, self.gaussian.y0)
        # self.shader_program.setUniformValue(self.width_x_uniform, self.gaussian.width_x)
        # self.shader_program.setUniformValue(self.width_y_uniform, self.gaussian.width_y)
        # self.shader_program.setUniformValue(self.rotation_uniform, self.gaussian.rotation)
        # self.shader_program.setUniformValue(self.shape_uniform, self._gaussian_shape)

        GL.glBindVertexArray(self.VAO)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

        GL.glBindVertexArray(0)
        self.shader_program.release()

    def paint_scale_bar(self, painter, half_width, half_height):
        painter.setPen(QPen(self._pen_colour(), self._scale_bar_thickness))
        half_scale_bar_width = self.scale_bar_width * 0.5

        start = QPointF(half_width - half_scale_bar_width, half_height)
        end = QPointF(half_width + half_scale_bar_width, half_height)

        painter.drawLine(QPointF(start.x(), start.y() - half_scale_bar_width), QPointF(start.x(), start.y() + half_scale_bar_width))
        painter.drawLine(start, end)
        painter.drawLine(QPointF(end.x(), end.y() - half_scale_bar_width), QPointF(end.x(), end.y() + half_scale_bar_width))

    def paintGL(self):

        if not self.gl_initialised:
            self.initializeGL()

        value = float(self.background_colour) / 255.0
        GL.glClearColor(value, value, value, 1.0)
        # GL.glClearColor(1.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.projection_matrix.setToIdentity()
        self.projection_matrix.ortho(0, self.width(), self.height(), 0, -1, 1)

        for drawable in self.drawables:
            drawable.paint_gl()
       # ar = self.width() / self.height()

        # if ar > 1:
        #     self.projection_matrix.ortho(-ar, ar, -1, 1, -1, 1)
        # else:
        #     self.projection_matrix.ortho(-1, 1, -ar, ar, -1, 1)
        #
        # if self._show_crosshair:
        #     self.crosshair.paint_gl(dx=self.dx,
        #                             dy=self.dy,
        #                             height=self.height(),
        #                             inverted=self.inverted,
        #                             projection_matrix=self.projection_matrix,
        #                             rotation=self.rotation,
        #                             thickness=self._crosshair_thickness,
        #                             width=self.width())
        # elif self._show_scale_bar:
        #     self.paint_scale_bar(painter=painter, half_width=half_x, half_height=half_y)
        # else:
        #     if self.image is not None and self.texture:
        #         self.paint_gl_image()

    def reset_background(self):
        self.set_background_colour(255.0 if self.inverted else 0.0)

    def resizeEvent(self, resize_event):
        super().resizeEvent(resize_event)
        self.resized.emit(resize_event)

    def rotate(self, value):
        self.rotation = value
        self.compute_transformation_matrix()
        self.update()

    def save(self):
        return {
            'dx': self.dx,
            'dy': self.dy,
            'scale': self.scale,
            'rotation': self.rotation
        }

    def set_scale(self, new_scale):
        self.scale = new_scale
        self.compute_transformation_matrix()
        self.update()

    def set_background_colour(self, value):
        value = int(value)

        if value == self._background_colour:
            return

        self._background_colour = value
        self.backgroundColourChanged.emit(value)
        self.update()

    def set_full_brightness(self):
        self.set_background_colour(self.full_brightness())

    def set_gaussian(self, gaussian, shape):
        self.gaussian = gaussian
        self._gaussian_shape.setX(shape[0])
        self._gaussian_shape.setY(shape[1])
        self.update()

    @property
    def scale_bar_thickness(self):
        return self._scale_bar_thickness

    @scale_bar_thickness.setter
    def scale_bar_thickness(self, new_thickness):
        self._scale_bar_thickness = new_thickness
        self.update()

    @property
    def scale_bar_width(self):
        return self._scale_bar_width

    @scale_bar_width.setter
    def scale_bar_width(self, new_width):
        self._scale_bar_width = new_width
        self.update()

    def showEvent(self, event):
        self.shown.emit()

    def hide_crosshair(self):
        self._show_crosshair = False
        self.update()

    def show_crosshair(self):
        self._show_scale_bar = False
        self.set_background_colour(255.0 if self.inverted else 0.0)
        self._show_crosshair = True
        self.update()

    @property
    def show_scale_bar(self):
        return self._show_scale_bar

    @show_scale_bar.setter
    def show_scale_bar(self, new_value):
        self._show_scale_bar = new_value
        if self._show_scale_bar:
            self._show_crosshair = False
        self.update()

    def translate(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.compute_transformation_matrix()
        self.update()

    def toggle_crosshair(self):
        self.hide_crosshair() if self._show_crosshair else self.show_crosshair()
        return self._show_crosshair

    def toggle_widget(self):
        self.close() if self.isVisible() else self.open()

    @property
    def use_homography(self):
        return self._use_homography

    @use_homography.setter
    def use_homography(self, value):
        self._use_homography = value
        self.update_image()

    @property
    def use_intensity_mask(self):
        return self._use_intensity_mask

    @use_intensity_mask.setter
    def use_intensity_mask(self, new_value):
        self._use_intensity_mask = new_value
        self.update_image()

    def update_image(self):

        img = self._image

        if img is not None:
            if self._use_intensity_mask:
                mask = cv2.resize(self.intensity_mask, img.shape)
                img = img * mask

            if self._use_homography:
                height, width = img.shape
                img = cv2.warpPerspective(img, self.homography_transform.matrix, (height, width))

        self.image_to_upload = img
        self.texture_uploaded = False
        self.update()


VERTEX_INTENSITY = """#version 330
        in vec3 vertexPosition;
        in vec2 vertexTexCoords;
        
        out vec2 textureCoords;

        void main() {
           gl_Position = vec4(vertexPosition, 0.0);
            textureCoords = vertexTexCoords;
        }"""

FRAGMENT_INTENSITY = """#version 330
        in vec2 textureCoords;
        uniform sampler2D texture_framebuffer;
        out vec4 colour;

        uniform float centre_x = 678;
        uniform float centre_y = 987;        
        uniform float height = 213;
        uniform float rotation = 26;
        uniform float max_height;
        uniform vec2 shape;
        uniform float width_x = 231;
        uniform float width_y = 254;

        float gaussianMask(float x, float y)
        {
            float rotation_radians = radians(rotation);

            float centre_x2 = centre_x * cos(rotation_radians) - centre_y * sin(rotation_radians);
            float centre_y2 = centre_x * sin(rotation_radians) + centre_y * cos(rotation_radians);

            float xp = x * cos(rotation_radians) - y * sin(rotation_radians);
            float yp = x * sin(rotation_radians) + y * cos(rotation_radians);

           float a = pow((centre_x2 - xp) / width_x, 2);
           float b = pow((centre_y2 - yp) / width_y, 2);

            float gaussian = height * exp(-0.5 * (a + b));

            return (1.0 - gaussian / height);
        }

        void main() {
             colour = texture(texture_framebuffer, textureCoords) * gaussianMask(gl_FragCoord.x, gl_FragCoord.y);
             //vec2 blah = textureCoords;
             //colour = vec4(1.0, 0.0, 0.0, 1.0);
             

             /* if (intensity_mask)
              {
              vec3 transformed = homography_matrix * vec3(textureCoords.x, textureCoords.y, 1.0);

                  float y = transformed.x;// * shape.y;
                  float x = (1 - transformed.y);// * shape.x;

                    colour.xyz = vec3(gaussianMask(x,  y));
                    colour = colour * gaussianMask();
               }*/

        }"""


class StimulusWindowGraphicsView(QGraphicsView, InvertSceneColoursMixin):

    visibilityChanged = pyqtSignal(bool)

    def __init__(self,  homography_transform, intensity_mask, parent=None):
        super().__init__(parent)
        self._crosshair = False
        self._crosshair_thickness = 1
        self._apply_intensity_mask = False
        self._invert = False
        self.setViewport(QOpenGLWidget())
        self.gaussian_shader_program = QOpenGLShaderProgram()
        self.homography_transform = homography_transform
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalScrollBar().disconnect()
        self.verticalScrollBar().disconnect()
        self.intensity_mask = intensity_mask

        self.intensity_mask_renderer = GaussianIntensityMaskRenderer(parent=self)

        # background_brush = QBrush()
        # background_brush.setStyle(Qt.SolidPattern)
        # background_brush.setColor(Qt.black)
        # self.setBackgroundBrush(background_brush)

        self.horizontal_line = QGraphicsLineItem()
        self.vertical_line = QGraphicsLineItem()

        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        self.horizontal_line.setLine(0, 1080/2, 1920, 1080/2)
        self.vertical_line.setLine(1920/2, 0, 1920/2, 1080)

        self.pen = QPen(Qt.white)
        self.horizontal_line.setPen(self.pen)
        self.vertical_line.setPen(self.pen)

        self.view_matrix = QMatrix4x4()
        self.dx = 0
        self.dy = 0
        self.angle = 0
        self.scale_value = 1

        self.setSceneRect(0, 0, 9000, 9000)

        # x0 = -1
        # y0 = -1
        # width = 2
        #
        # self.vertex_data = np.array([
        #     x0, y0, 0.0,                    0.0, 0.0,
        #     x0 + width, y0, 0.0,            1.0, 0.0,
        #     x0 + width, y0 + width, 0.0,    1.0, 1.0,
        #
        #     x0 + width, y0 + width, 0.0,    1.0, 1.0,
        #     x0, y0 + width, 0.0,            0.0, 1.0,
        #     x0, y0, 0.0,                    0.0, 0.0
        # ], dtype=np.float32)
        #
        # self.intensity_mask_initialised = False

    @property
    def apply_intensity_mask(self):
        return self._apply_intensity_mask

    @apply_intensity_mask.setter
    def apply_intensity_mask(self, value):
        log.debug("apply_intensity_mask setter")
        self._apply_intensity_mask = value
        self.scene().update()

    @property
    def crosshair(self):
        return self._crosshair

    @crosshair.setter
    def crosshair(self, value):
        self._crosshair = value
        self.scene().update()

    @property
    def crosshair_thickness(self):
        return self._crosshair_thickness

    @crosshair_thickness.setter
    def crosshair_thickness(self, thickness):
        self._crosshair_thickness = thickness
        self.scene().update()

    def draw_crosshair(self, painter, rect):
        log.debug("draw crosshair")
        pen = QPen(Qt.white)
        pen.setWidth(self.crosshair_thickness)

        # log.debug("rect centre at {}".format(self.mapFromScene(rect.center())))
        log.debug(rect.left())

        painter.setPen(pen)
       # painter.setTransform(self.view_matrix.toTransform())
        painter.drawLine(-9999, rect.center().y() + self.dy, 9999, rect.center().y() + self.dy)
        painter.drawLine(rect.center().x() + self.dx, -9999, rect.center().x() + self.dx, 9999)

    def drawBackground(self, painter, rect):
        if not self.initialised:
            self.initialise_gl()

        # if not self.intensity_mask_renderer.initialised:
        #     self.intensity_mask_renderer.initialise_gl()

        if self.recreate_frame_buffer:
            self.resize_texture()

        if self.invert:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frame_buffer)

        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        super().drawBackground(painter, rect)

    def drawForeground(self, painter, rect):
        if self.crosshair:
            self.draw_crosshair(painter, rect)

        if self.apply_intensity_mask:
            log.debug("apply_intensity_mask")
            self.intensity_mask_renderer.draw()
            # self.draw_intensity_mask()

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.viewport().defaultFramebufferObject())

        if self.invert:
            self.draw_texture_to_screen()

    # def init_intensity_mask_gl(self):
    #
    #     self.viewport().makeCurrent()
    #     #log.debug("init_intensity_mask_gl")
    #
    #     self.gaussian_shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_INTENSITY)
    #     self.gaussian_shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT_INTENSITY)
    #
    #     if not self.gaussian_shader_program.link():
    #         raise Exception("Could not link shaders - {}".format(self.gaussian_shader_program.log()))
    #
    #     self.intensity_mask_vao = GL.glGenVertexArrays(1)
    #     GL.glBindVertexArray(self.intensity_mask_vao)
    #
    #     vertex_buffer_object = GL.glGenBuffers(1)
    #     GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
    #     GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
    #                     GL.GL_STATIC_DRAW)
    #
    #     self.vertex_position = self.gaussian_shader_program.attributeLocation("vertexPosition")
    #     self.texture_coords = self.gaussian_shader_program.attributeLocation("vertexTexCoords")
    #     self.texture_framebuffer = self.gaussian_shader_program.uniformLocation("texture_framebuffer")
    #
    #     self.centre_x_uniform = self.gaussian_shader_program.uniformLocation("centre_x")
    #     self.centre_y_uniform = self.gaussian_shader_program.uniformLocation("centre_y")
    #     self.height_uniform = self.gaussian_shader_program.uniformLocation("height")
    #     self.rotation_uniform = self.gaussian_shader_program.uniformLocation("rotation")
    #     self.max_height_uniform = self.gaussian_shader_program.uniformLocation("max_height")
    #     self.shape_uniform = self.gaussian_shader_program.uniformLocation("shape")
    #     self.width_x_uniform = self.gaussian_shader_program.uniformLocation("width_x")
    #     self.width_y_uniform = self.gaussian_shader_program.uniformLocation("width_y")
    #
    #     GL.glEnableVertexAttribArray(0)
    #     GL.glEnableVertexAttribArray(1)
    #     GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 20,
    #                              None)
    #
    #     GL.glVertexAttribPointer(self.texture_coords, 2, GL.GL_FLOAT, GL.GL_TRUE, 20,
    #                              ctypes.c_void_p(12))
    #     GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    #     GL.glBindVertexArray(0)
    #
    #     # frame buffer
    #     self.intensity_mask_texture = GL.glGenTextures(1)
    #     GL.glBindTexture(GL.GL_TEXTURE_2D, self.intensity_mask_texture)
    #     GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
    #     GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    #
    #     GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.width(), self.height(), 0,
    #                     GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
    #
    #     #GL.glDeleteFramebuffers([self.frame_buffer])
    #     self.intensity_mask_framebuffer = GL.glGenFramebuffers(1)
    #     GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.intensity_mask_framebuffer)
    #
    #     GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, self.intensity_mask_framebuffer, 0)
    #
    #     self.intensity_mask_initialised = True

    # def draw_intensity_mask(self):
    #     log.debug("draw_intensity_mask")
    #     self.gaussian_shader_program.bind()
    #     GL.glBindVertexArray(self.intensity_mask_vao)
    #     GL.glActiveTexture(GL.GL_TEXTURE0)
    #     GL.glBindTexture(GL.GL_TEXTURE_2D, self.intensity_mask_texture)
    #     #self.gaussian_shader_program.setUniformValue(self.texture_framebuffer, self.
    #     GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
    #     GL.glBindVertexArray(0)
    #     self.gaussian_shader_program.release()

    def hideEvent(self, event):
        self.visibilityChanged.emit(False)

    @property
    def invert(self):
        return self._invert

    @invert.setter
    def invert(self, value):
        self._invert = value
        self.scene().update()

    def mousePressEvent(self, event):
        event.ignore()

    def open(self):
        desktop = QApplication.desktop()
        is_fullscreen = desktop.screenCount() > 1

        other_screen_x = 1024
        other_screen_x = 1024

        if is_fullscreen:
            screen_widget_on = desktop.screenNumber(QApplication.activeWindow())
            next_screen_not_in_use = (screen_widget_on + 1) % desktop.screenCount()
            other_screen_geometry = desktop.screenGeometry(next_screen_not_in_use)
            self.move(other_screen_geometry.x(), other_screen_geometry.y())
            self.showFullScreen()
        else:
            self.resize(1024, 1024)
            self.show()
        self.scene().setSceneRect(0, 0, other_screen_geometry.width(), other_screen_geometry.height())

        # self.scene().setSceneRect(-other_screen_geometry.width() / 2,
        #                           -other_screen_geometry.height() / 2,
        #                           other_screen_geometry.width(),
        #                           other_screen_geometry.height())
        #self.scene().setSceneRect(0, 0, other_screen_geometry.width(), other_screen_geometry.height())
        self.scene().update_background()
        #self.scene().background_image.setPos(self.scene().sceneRect().topLeft())
        self.showFullScreen() if is_fullscreen else self.show()
        self.centerOn(self.scene().sceneRect().center())

    def set_rotation(self, angle):
        self.angle = angle
        self.compute_transformation_matrix()
        self.setTransform(self.view_matrix.toTransform())

    def set_scale(self, scale):
        self.scale_value = scale
        self.compute_transformation_matrix()
        self.setTransform(self.view_matrix.toTransform())

    def set_translation(self, dx, dy):
        self.dx = dx
        self.dy = dy
        self.compute_transformation_matrix()
        self.setTransform(self.view_matrix.toTransform())

    def showEvent(self, event):
        self.visibilityChanged.emit(True)

    def toggle(self):
        self.close() if self.isVisible() else self.open()

    def compute_transformation_matrix(self):
        self.view_matrix.setToIdentity()
        rect = self.scene().sceneRect()
        self.view_matrix.translate(rect.center().x() + self.dx, rect.center().y() + self.dy, 0)
        self.view_matrix.scale(self.scale_value)
        self.view_matrix.rotate(self.angle, QVector3D(0, 0, 1))
        self.view_matrix.translate(-rect.center().x() - self.dx, -rect.center().y() - self.dy, 0)
        self.view_matrix.translate(self.dx, self.dy, 0)

    def wheelEvent(self, event):
        if not self.scene().selectedItems():
            self.zoom(event)
            return
        return super().wheelEvent(event)

    # def zoom(self, event):
    #     zoomInFactor = 1.25
    #     zoomOutFactor = 1 / zoomInFactor
    #     # Save the scene pos
    #     oldPos = self.mapToScene(event.pos())
    #     # Zoom
    #     if event.angleDelta().y() > 0:
    #         zoomFactor = zoomInFactor
    #     else:
    #         zoomFactor = zoomOutFactor
    #     self.scale(zoomFactor, zoomFactor)
    #     # Get the new position
    #     newPos = self.mapToScene(event.pos())
    #     # Move scene to old position
    #     delta = newPos - oldPos
    #  #   log.debug("event pos: {}, Old Pos: {}, new pos {}".format(event.pos(), oldPos, newPos))
    #     self.translate(delta.x(), delta.y())

    def apply_transform(self, transform):
        #log.debug("apply_transform")
        t = QMatrix4x4(transform)
        view_matrix = QMatrix4x4()
        rect = self.scene().sceneRect()
        view_matrix.translate(rect.center().x() + self.dx, rect.center().y() + self.dy, 0)
        #view_matrix.scale(self.scale_value)
        #view_matrix.rotate(self.angle, QVector3D(0, 0, 1))
        view_matrix = t * view_matrix# * t
        view_matrix.translate(-rect.center().x() - self.dx, -rect.center().y() - self.dy, 0)
        #view_matrix.translate(self.dx, self.dy, 0)
        self.setTransform(transform)
        # self.setTransform(view_matrix.toTransform())



