import sys

from OpenGL import GL
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QMatrix4x4, QVector3D
from PyQt5.QtWidgets import QOpenGLWidget, QApplication, QGraphicsView, QGraphicsScene

from optostim.graphics.quad import Quad


class Square(QObject):

    positionChanged = pyqtSignal()

    def __init__(self, parent, position=(0,0), scale=1.0):
        super().__init__(parent)
        self._position = position
        self.pixel_size = scale
        self.projection_matrix = QMatrix4x4()
        self.render = Quad(parent=self)
        self.model_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self._update_model_matrix()

    def draw(self, projection=QMatrix4x4(), view=QMatrix4x4()):
        self.projection_matrix = projection
        self.view_matrix = view
        self.render.paint_gl(projection_matrix=projection, view_matrix=view, model_matrix=self.model_matrix)
        transformation_matrix = self.projection_matrix * self.view_matrix * self.model_matrix
        transformed_origin = transformation_matrix * QVector3D(0, 0, 0)

    def is_point_inside(self, x, y):
        transformation_matrix = self.projection_matrix * self.view_matrix * self.model_matrix
        inverse_transform = transformation_matrix.inverted()
        #  todo take account of view

        transformed_coordinates = inverse_transform[0] * QVector3D(x, y, 0)
        return 0 <= transformed_coordinates.x() <= 1 and 0 <= transformed_coordinates.y() <= 1

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, new_pos):
        self._position = new_pos
        self._update_model_matrix()

    def _update_model_matrix(self):
        self.model_matrix = QMatrix4x4()
        self.model_matrix.scale(self.pixel_size)

        dx = self.position[0] / self.pixel_size
        dy = self.position[1] / self.pixel_size

        self.model_matrix.translate(dx, dy)

    def __repr__(self):
        position = self.projection_matrix * self.view_matrix * self.model_matrix * QVector3D(0, 0, 0)
        return "Square at ({}, {})".format(position.x(), position.y())


class TestSquares(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)


class OpenGLWidget(QOpenGLWidget):

    squaresChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        #size on stimulus widget
        pixel_size = 50
        self.squares = [Square(parent=self, position=(pixel_size, pixel_size), scale=pixel_size),
                        Square(parent=self, position=(100, pixel_size), scale=pixel_size),
                        Square(parent=self, position=(200, 100), scale=pixel_size),
                        Square(parent=self, position=(300, 100), scale=pixel_size)
                        ]
        self.square_to_drag = None
        self.stimulus_window = None
        print("Init complete")

    def drag_square(self):
        pass

    def mouseMoveEvent(self, event):
        try:
            # x = max(event.x(), self.square_to_drag.pixel_size)
            # y = max(event.y(), self.square_to_drag.pixel_size)
            self.square_to_drag.position = (event.x(), event.y())
            self.update()
            print("You drag")
        except AttributeError:
            pass

    def mousePressEvent(self, event):
        print("mouse press event {}".format(event.windowPos()))
        self.is_dragging = True
        for square in self.squares:
            x = 2 * event.x() / self.width() - 1
            y = -2 * event.y() / self.height() + 1
            if square.is_point_inside(x, y):
                print("Found it, square at {}".format(square.position))
                self.square_to_drag = square
                break

    def mouseReleaseEvent(self, event):
        self.square_to_drag = None

    def initializeGL(self):
        print("InitGL")
        for square in self.squares:
            square.render.initialise_gl()
        print("InitGL complete")

    def paintGL(self):
        print("Begin paint")
        GL.glClearColor(0, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projection_matrix = QMatrix4x4()
        projection_matrix.ortho(0, self.width(), self.height(), 0, -1, 1)

        squares_for_sw = []
        scale_y = self.stimulus_window.height() / self.height()
        scale_x = self.stimulus_window.width() / self.width()

        view_matrix = QMatrix4x4()
      #  view_matrix.scale(1 / scale_x, 1 / scale_y)

        for square in self.squares:
            x = square.position[0] * scale_x
            y = square.position[1] * scale_y

            squares_for_sw.append(Square(parent=self.stimulus_window,
                                         position=(x, y),
                                         scale=square.pixel_size))
            square.draw(projection=projection_matrix, view=view_matrix)

        self.stimulus_window.drawables = squares_for_sw

    def resizeGL(self, width, height):
        print("Old {} {}, new {} {}".format(self.width(), self.height(), width, height))


class StimulusWindow(QOpenGLWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drawables = []
        self.gl_needs_init = True

    def initializeGL(self):
        for drawable in self._drawables:
            drawable.render.initialise_gl()
        self.gl_needs_init = False

    def paintGL(self):

        if self.gl_needs_init:
            self.initializeGL()

        GL.glClearColor(0, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projection_matrix = QMatrix4x4()
        projection_matrix.ortho(0, self.width(), self.height(), 0, -1, 1)

        for drawable in self.drawables:
            drawable.draw(projection=projection_matrix)

    # def showEvent(self, *args, **kwargs):
    #     desktop = QApplication.desktop()
    #     is_fullscreen = desktop.screenCount() > 1
    #
    #     if is_fullscreen:
    #         screen_widget_on = desktop.screenNumber(QApplication.activeWindow())
    #         next_screen_not_in_use = (screen_widget_on + 1) % desktop.screenCount()
    #         other_screen_geometry = desktop.screenGeometry(next_screen_not_in_use)
    #         self.move(other_screen_geometry.x(), other_screen_geometry.y())
    #         self.showFullScreen()
    #     else:
    #         self.resize(1024, 1024)
    #         self.show()
    #
    #     self.showFullScreen() if is_fullscreen else self.show()

    @property
    def drawables(self):
        return self._drawables

    @drawables.setter
    def drawables(self, new_drawables):
        self._drawables = new_drawables
        self.gl_needs_init = True
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    camera_window = [(0, 0), (1360, 0), (1360, 1036), (0, 1036)]

    # pixel_size = 100
    # squares = [Square(parent=None, position=(0.0, 10), scale=pixel_size),
    #            Square(parent=None, position=(100, 100), scale=pixel_size)]

    myapp = OpenGLWidget()

    myapp.frameSwapped.connect(lambda: print("Swapped"))
    sw = StimulusWindow()

    sw.setWindowTitle("Stimulus Window")

    myapp.stimulus_window = sw

    sw.show()
    myapp.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)