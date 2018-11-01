import ctypes

import numpy as np
from OpenGL import GL
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader

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
             vec4 c = texture(texture_framebuffer, textureCoords) * gaussianMask(gl_FragCoord.x, gl_FragCoord.y);
             //vec2 blah = textureCoords;
             colour = vec4(1.0, 0.0, 0.0, 1.0);


             /* if (intensity_mask)
              {
              vec3 transformed = homography_matrix * vec3(textureCoords.x, textureCoords.y, 1.0);

                  float y = transformed.x;// * shape.y;
                  float x = (1 - transformed.y);// * shape.x;

                    colour.xyz = vec3(gaussianMask(x,  y));
                    colour = colour * gaussianMask();
               }*/

        }
"""


class GaussianIntensityMaskRenderer(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.framebuffer = None
        self.shader_program = QOpenGLShaderProgram()
        self.texture = None
        self.vertex_attribute_object = None

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

        self.initialised = False

    def draw(self):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.framebuffer)
        self.shader_program.bind()
        GL.glBindVertexArray(self.vertex_attribute_object)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.shader_program.release()

    def initialise_gl(self):
        self.initialise_shader()
        self.initialise_texture()
        self.initialise_framebuffer()
        self.initialised = True

    def initialise_framebuffer(self):
        self.framebuffer = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.framebuffer)
        GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT1, self.framebuffer, 0)

    def initialise_shader(self):
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_INTENSITY)
        self.shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT_INTENSITY)

        if not self.shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.shader_program.log()))

        self.vertex_attribute_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vertex_attribute_object)

        vertex_buffer_object = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        self.vertex_position = self.shader_program.attributeLocation("vertexPosition")
        self.texture_coords = self.shader_program.attributeLocation("vertexTexCoords")
        self.texture_framebuffer = self.shader_program.uniformLocation("texture_framebuffer")

        self.centre_x_uniform = self.shader_program.uniformLocation("centre_x")
        self.centre_y_uniform = self.shader_program.uniformLocation("centre_y")
        self.height_uniform = self.shader_program.uniformLocation("height")
        self.rotation_uniform = self.shader_program.uniformLocation("rotation")
        self.max_height_uniform = self.shader_program.uniformLocation("max_height")
        self.shape_uniform = self.shader_program.uniformLocation("shape")
        self.width_x_uniform = self.shader_program.uniformLocation("width_x")
        self.width_y_uniform = self.shader_program.uniformLocation("width_y")

        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(self.vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 20,
                                 None)

        GL.glVertexAttribPointer(self.texture_coords, 2, GL.GL_FLOAT, GL.GL_TRUE, 20,
                                 ctypes.c_void_p(12))
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def initialise_texture(self):
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.parent().width(), self.parent().height(), 0,
                        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)