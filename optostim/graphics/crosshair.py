import logging

import numpy as np
from OpenGL import GL
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader, QMatrix4x4, QVector3D, QPen
from PyQt5.QtWidgets import QGraphicsLineItem

log = logging.getLogger(__name__)

# todo - Even thickness, translate to edges properly

VERTEX = '''
    #version 330
    in vec3 vertexPosition;
    uniform mat4 projection_matrix;
    uniform mat4 view_matrix;
    out mat4 transformation;

    void main()
    {
        transformation = projection_matrix * view_matrix; 
        gl_Position = transformation * vec4(vertexPosition, 1.0);
    }
'''

FRAGMENT = '''
    #version 330
    out vec4 colour;
    uniform bool inverted;
    in mat4 transformation;
    //uniform vec2 screen_resolution;
    
    void main()
    {
        colour = vec4(1.0);
        
        if (inverted){
            colour = vec4(1.0 - colour.r, 1.0 - colour.g, 1.0 - colour.b, 1.0); 
        }
    }
'''


class CrosshairLine(QObject):

    def __init__(self, parent, vertex_data):
        super().__init__(parent)
        self.shader_program = QOpenGLShaderProgram(parent=self)
        self.vertex_attribute_object = None
        self.vertex_data = vertex_data
        self.vertex_position_uniform = None

    def get_uniform_location(self, name):
        location = self.shader_program.uniformLocation(name)
        if location == -1:
            raise ValueError("Uniform {} has no location.".format(name))
        return location

    def initialise_gl(self):
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX)
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT)

        if not self.shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.shader_program.log()))

        self.vertex_attribute_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertex_attribute_object)

        vertex_buffer_object = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        self.vertex_position = self.shader_program.attributeLocation("vertexPosition")

        self.inverted_uniform = self.get_uniform_location("inverted")
        self.projection_matrix_uniform = self.get_uniform_location("projection_matrix")
        self.view_matrix_uniform = self.get_uniform_location("view_matrix")

        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def paint_gl(self, inverted, projection_matrix, view_matrix):
        self.shader_program.bind()
        self.shader_program.setUniformValue(self.inverted_uniform, inverted)
        self.shader_program.setUniformValue(self.projection_matrix_uniform, projection_matrix)
        self.shader_program.setUniformValue(self.view_matrix_uniform,  view_matrix)
        GL.glBindVertexArray(self.vertex_attribute_object)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.shader_program.release()


class Crosshair(QObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.loc = 1.0
        corner = 10.0
        horizontal_vertices = np.array([
            -corner, self.loc, 0.1,
            corner, self.loc, 0.1,
            corner, -self.loc, 0.1,

            corner, -self.loc, 0.1,
            -corner, -self.loc, 0.1,
            -corner, self.loc, 0.1
        ], dtype=np.float32)

        vertical_vertices = np.array([
            -self.loc, corner, 0.1,
            self.loc, corner, 0.1,
            self.loc, -corner, 0.1,

            self.loc, -corner, 0.1,
            -self.loc, -corner, 0.1,
            -self.loc, corner, 0.1
        ], dtype=np.float32)
        self.vertical_line = CrosshairLine(parent=self, vertex_data=vertical_vertices)
        self.horizontal_line = CrosshairLine(parent=self, vertex_data=horizontal_vertices)
        self.view_matrix = QMatrix4x4()

    def initialise_gl(self):
        self.horizontal_line.initialise_gl()
        self.vertical_line.initialise_gl()

    def paint_gl(self, dx, dy, height, inverted, thickness, projection_matrix, rotation, width):

        scale_x = thickness * 2.0 * self.loc / width
        scaly_y = thickness * 2.0 * self.loc / height

        dx = dx / (0.5 * width)
        dy = - dy / (0.5 * height)

        log.debug("dx={}, dy={}".format(dx, dy))

        view_matrix = QMatrix4x4()
        view_matrix.translate(dx, dy)
        view_matrix.rotate(rotation, QVector3D(0, 0, 1))
        view_matrix.scale(scale_x, 1)

        self.vertical_line.paint_gl(inverted, projection_matrix, view_matrix)

        view_matrix2 = QMatrix4x4()
        view_matrix2.translate(dx, dy)
        view_matrix2.rotate(rotation, QVector3D(0, 0, 1))
        view_matrix2.scale(1, scaly_y)

        self.horizontal_line.paint_gl(inverted, projection_matrix, view_matrix2)


class CrosshairGraphicsItem(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.horizontal_line = QGraphicsLineItem()
        self.vertical_line = QGraphicsLineItem()

        self.horizontal_line.setLine(0, 1080/2, 1920, 1080/2)
        self.vertical_line.setLine(1920/2, 0, 1920/2, 1080)

        self.pen = QPen(Qt.white)
        self.horizontal_line.setPen(self.pen)
        self.vertical_line.setPen(self.pen)


