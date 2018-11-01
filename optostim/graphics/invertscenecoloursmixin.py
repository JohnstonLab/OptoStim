import ctypes

import numpy as np
from OpenGL import GL
from PyQt5.QtGui import QOpenGLShader, QOpenGLShaderProgram

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


class InvertSceneColoursMixin:

    def __init__(self):
        self.initialised = False
        self.shader_program = QOpenGLShaderProgram()
        self.vertex_position = None
        self.texture = 0
        self.frame_buffer = 0
        self.recreate_frame_buffer = True

        x0 = -1
        y0 = -1
        width = 2

        self.vertex_data = np.array([
            x0, y0, 0.0,                    0.0, 0.0,
            x0 + width, y0, 0.0,            1.0, 0.0,
            x0 + width, y0 + width, 0.0,    1.0, 1.0,

            x0 + width, y0 + width, 0.0,    1.0, 1.0,
            x0, y0 + width, 0.0,            0.0, 1.0,
            x0, y0, 0.0,                    0.0, 0.0
        ], dtype=np.float32)

    def draw_texture_to_screen(self):
        self.shader_program.bind()
        GL.glBindVertexArray(self.vertex_attribute_object)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.shader_program.release()

    def create_framebuffer(self):
      #  log.debug("create_framebuffer")
        GL.glDeleteTextures([self.texture])
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.width(), self.height(), 0,
                        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)

        GL.glDeleteFramebuffers([self.frame_buffer])
        self.frame_buffer = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frame_buffer)

        GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, self.texture, 0)

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
        self.texture_coords = self.shader_program.attributeLocation("tex_coords")
        self.texture_framebuffer = self.shader_program.uniformLocation("texture_framebuffer")

        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 20,
                                 None)

        GL.glVertexAttribPointer(self.texture_coords, 2, GL.GL_FLOAT, GL.GL_TRUE, 20,
                                 ctypes.c_void_p(12))

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        self.create_framebuffer()
        self.initialised = True

    def resize_texture(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.width(), self.height(), 0,
                        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
        self.recreate_frame_buffer = False