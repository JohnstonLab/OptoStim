import numpy as np
from OpenGL import GL
from PyQt5.QtGui import QImage, QPainter, QOpenGLShaderProgram, QOpenGLShader
from PyQt5.QtWidgets import QOpenGLWidget
from pyqtgraph.widgets.RawImageWidget import RawImageWidget

LOC = 1.0

VERTEX = """
    #version 330
    layout(location=0) in vec3 vertexPosition;
    layout(location=1) in vec2 vertexTexCoords;
    uniform mat4 transformationMatrix;
    uniform mat4 projection_matrix;
    uniform mat4 view_matrix;
    out vec2 textureCoords;
    
    void main() {
       gl_Position = projection_matrix * view_matrix * vec4(vertexPosition, 1.0);
        textureCoords = vertexTexCoords;
    }
"""

FRAGMENT = """
    #version 330
    in vec2 textureCoords;
    uniform sampler2D textureSampler;
    out vec4 colour;
    uniform mat4 projection_matrix;
    uniform mat4 view_matrix;
    void main() {
          colour = texture(textureSampler, textureCoords);
          if (intensity_mask)
          {
                colour = colour * gaussianMask();
           }
       if (inverted)
       {
            colour = vec4(1.0 - colour.r, 1.0 - colour.g, 1.0 - colour.b, 1.0);
        }
    }
"""


class ImageOpenGLWidget(RawImageWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.shader_program = QOpenGLShaderProgram(self)
        self.vertex_data = np.array([
            # X,    Y,   Z     U,   V
            -LOC, LOC, 0.0, 0.0, 1.0,
            LOC, LOC, 0.0, 1.0, 1.0,
            LOC, -LOC, 0.0, 1.0, 0.0,

            LOC, -LOC, 0.0, 1.0, 0.0,
            -LOC, -LOC, 0.0, 0.0, 0.0,
            -LOC, LOC, 0.0, 0.0, 1.0,
        ], dtype=np.float32)

        self._image = None#QImage()
        self.vao = None
        self.vertex_position_uniform = -1
        self.

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image):
        self._image = new_image
        if self._image is not None:
            self.create_texture()
        self.update()

    def initializeGL(self):
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX)
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT)

        if not self.shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.shader_program.log()))

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)

        VBO = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, VBO)

        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        self.vertex_position_uniform = self.get_uniform_location("vertexPosition")

        self.projection_matrix_uniform = self.shader_program.uniformLocation("projection_matrix")
        self.view_matrix_uniform = self.shader_program.uniformLocation("view_matrix")

        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 20,
                                 None)

        GL.glVertexAttribPointer(texture_coords, 2, GL.GL_FLOAT, GL.GL_TRUE, 20,
                                 ctypes.c_void_p(12))

        self.texture_sampler = self.shader_program.uniformLocation("textureSampler")
        self.texture = GL.glGenTextures(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.drawImage(0, 0, self._image)

    def paintGL(self):
        self.shader_program.bind()

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glUniform1i(self.texture_sampler, 0)

        GL.glBindVertexArray(self.VAO)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)

        GL.glBindVertexArray(0)
        self.shader_program.release()