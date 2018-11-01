import sys

from OpenGL import GL
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader
from PyQt5.QtWidgets import QOpenGLWidget, QApplication
import numpy as np
from scipy.ndimage import imread

VERTEX = '''
    #version 330
    in vec3 vertexPosition;
    out vec2 texture_coord;

    void main()
    {
        gl_Position = vec4(vertexPosition, 1.0);
        texture_coord = vertexPosition.xy;
    }
'''

FRAGMENT = '''
    #version 330
    out vec4 colour;
   // uniform sampler2D texture_sampler;
    in vec2 texture_coord;

    void main()
    {
       // colour = texture(texture_sampler, texture_coord);
       colour = vec4(texture_coord.x, texture_coord.y, 0.0, 1.0);
      //colour = vec4(1.0, 0.0, 0.0, 1.0);
    }
'''

VERTEX_SCREEN = '''
    #version 330
    in vec3 vertexPosition;
    out vec2 texture_coord;

    void main()
    {
        texture_coord = vertexPosition.xy;
        gl_Position = vec4(vertexPosition, 1.0);
    }
'''

FRAGMENT_SCREEN = '''
    #version 330
    in vec2 texture_coord;
    out vec4 colour;
    uniform sampler2D texture_framebuffer;

    void main()
    {
       //colour = vec4(0.0, 1.0, 0.0, 1.0);
       colour = vec4(1.0) - texture(texture_framebuffer, texture_coord);
    }
'''


class OpenGLWidget(QOpenGLWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_shader_program = QOpenGLShaderProgram()
        self.screen_shader_program = QOpenGLShaderProgram()
        x0 = -0.5
        y0 = -0.5
        width = 1

        self.vertex_data = np.array([
            x0, y0, 0.0,
            x0 + width, y0, 0.0,
            x0 + width, y0 + width, 0.0,

            x0 + width, y0 + width, 0.0,
            x0, y0 + width, 0.0,
            x0, y0, 0.0,
        ], dtype=np.float32)

    def create_render_target(self):
        render_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, render_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.width(), self.height(), 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

        fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)

        GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, render_texture, 0)

        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Framebuffer creation failed")

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        return fbo, render_texture

    def create_screen_shader_program(self):
        self.screen_shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_SCREEN)
        self.screen_shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT_SCREEN)

        if not self.screen_shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.screen_shader_program.log()))

        self.screen_vertex_attribute_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.screen_vertex_attribute_object)

        vertex_buffer_object = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        self.screen_vertex_position = self.screen_shader_program.attributeLocation("vertexPosition")
        self.screen_texture_coords = self.screen_shader_program.attributeLocation("texture_coords")
        self.texture_framebuffer = self.screen_shader_program.uniformLocation("texture_framebuffer")

        GL.glVertexAttribPointer(self.screen_vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        self.fbo, self.screen_texture = self.create_render_target()

    def create_scene_shader_program(self):
        self.scene_shader_program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX)
        self.scene_shader_program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAGMENT)

        if not self.scene_shader_program.link():
            raise Exception("Could not link shaders - {}".format(self.scene_shader_program.log()))

        self.scene_vertex_attribute_object = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.scene_vertex_attribute_object)

        vertex_buffer_object = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer_object)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertex_data.nbytes, self.vertex_data,
                        GL.GL_STATIC_DRAW)

        self.scene_vertex_position = self.scene_shader_program.attributeLocation("vertexPosition")
        assert self.scene_vertex_position != -1
        # self.texture_coords = self.shader_program.attributeLocation("texture_coords")
        # self.texture_framebuffer = self.shader_program.uniformLocation("texture_framebuffer")

        GL.glVertexAttribPointer(self.scene_vertex_position, 3, GL.GL_FLOAT, GL.GL_FALSE, 0,
                                 None)

        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

       # self.scene_texture = self.texture_from_image(imread("image-2018-01-31_15-40-12.png"))


    def create_texture(self):
       # GL.glActiveTexture(GL.GL_TEXTURE0)

        texture = GL.glGenTextures(1)

       # GL.glActiveTexture(GL.GL_TEXTURE0)
        #GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)

        #GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
        #GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, self.width(), self.height(), 0,
                        GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
       # GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return texture

    def initializeGL(self):
        print("Create scene shader")
        self.create_scene_shader_program()
        print("Create screen shader")
        self.create_screen_shader_program()
        print("InitGL complete")
       # self.create_render_target()

    def paintGL(self):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        self.paint_quad()
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.defaultFramebufferObject())

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.paint_to_screen()

    def paint_to_screen(self):
        print("Paint to screen")
        self.screen_shader_program.bind()
        GL.glBindVertexArray(self.screen_vertex_attribute_object)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.screen_texture)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.screen_shader_program.release()
        print("Paint to screen complete")
       # GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def paint_quad(self):
        self.scene_shader_program.bind()
       # GL.glActiveTexture(GL.GL_TEXTURE0)
        #GL.glBindTexture(GL.GL_TEXTURE_2D, self.scene_texture)
        GL.glBindVertexArray(self.scene_vertex_attribute_object)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        GL.glBindVertexArray(0)
        self.scene_shader_program.release()

    def texture_from_image(self, image):
        img_data = np.flipud(image)
        height, width = img_data.shape
        texture = GL.glGenTextures(1)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)

        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, width, height, 0,
                        GL.GL_LUMINANCE, GL.GL_UNSIGNED_BYTE, img_data)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return texture

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OpenGLWidget()

    w.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)