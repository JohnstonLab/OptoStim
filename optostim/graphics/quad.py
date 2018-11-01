import numpy as np
from OpenGL import GL
from PyQt5.QtCore import QObject, QRectF
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader, QMatrix4x4
from PyQt5.QtWidgets import QGraphicsRectItem

VERTEX = '''
    #version 330
    in vec3 vertexPosition;
    uniform mat4 model_matrix;
    uniform mat4 projection_matrix;
    uniform mat4 view_matrix;
    out mat4 transformation;

    void main()
    {
        transformation = projection_matrix * view_matrix * model_matrix; 
        gl_Position = transformation * vec4(vertexPosition, 1.0);
    }
'''

FRAGMENT = '''
    #version 330
    out vec4 colour;
    in mat4 transformation;
    //uniform vec2 screen_resolution;

    void main()
    {
        colour = vec4(1.0);
    }
'''


class GLGraphicsRectItem(QGraphicsRectItem):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shader_program = QOpenGLShaderProgram()
        width = 1
        half_width = width / 2
        rect = QRectF(-half_width, -half_width, width, width)
        self.setRect(rect)
        self.vertex_attribute_object = None
        self.vertex_data = np.array([
            -half_width, -half_width, 0.0,
            -half_width + width, -half_width, 0.0,
            -half_width + width, -half_width + width, 0.0,

            -half_width + width, -half_width + width, 0.0,
            -half_width, half_width, 0.0,
            -half_width, -half_width, 0.0
        ], dtype=np.float32)
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

        self.projection_matrix_uniform = self.get_uniform_location("projection_matrix")
        self.view_matrix_uniform = self.get_uniform_location("view_matrix")
        self.model_matrix_uniform = self.get_uniform_location("model_matrix")

        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def paint_gl(self):

        model_matrix = QMatrix4x4()
        projection_matrix = QMatrix4x4()
        view_matrix = QMatrix4x4()

        self.shader_program.bind()
        self.shader_program.setUniformValue(self.model_matrix_uniform, model_matrix)
        self.shader_program.setUniformValue(self.projection_matrix_uniform, projection_matrix)
        self.shader_program.setUniformValue(self.view_matrix_uniform, view_matrix)
        GL.glBindVertexArray(self.vertex_attribute_object)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.shader_program.release()


class Quad(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.shader_program = QOpenGLShaderProgram(parent=self)
        self.inverted = False
        self.vertex_attribute_object = None
        self.vertex_data = np.array([
            0.0, 1.0, 0.0,
            1.0, 1.0, 0.0,
            1.0, 0.0, 0.0,

            1.0, 0.0, 0.0,
            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0
        ], dtype=np.float32)
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

        self.projection_matrix_uniform = self.get_uniform_location("projection_matrix")
        self.view_matrix_uniform = self.get_uniform_location("view_matrix")
        self.model_matrix_uniform = self.get_uniform_location("model_matrix")

        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def paint_gl(self, projection_matrix, view_matrix, model_matrix):
        self.shader_program.bind()
        self.shader_program.setUniformValue(self.model_matrix_uniform, model_matrix)
        self.shader_program.setUniformValue(self.projection_matrix_uniform, projection_matrix)
        self.shader_program.setUniformValue(self.view_matrix_uniform,  view_matrix)
        GL.glBindVertexArray(self.vertex_attribute_object)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.shader_program.release()