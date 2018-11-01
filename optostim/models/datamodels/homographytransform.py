import logging

import numpy as np
import pandas
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTransform, QMatrix4x4

log = logging.getLogger(__name__)


class HomographyTransform(QObject):

    matrixChanged = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._matrix = np.identity(3)
        self.transform = QTransform()
        self.matrix4x4 = QMatrix4x4()

    def __getstate__(self):
        return {'matrix': pandas.DataFrame(self.matrix).to_json()}

    def __setstate__(self, state):
        self.matrix = pandas.read_json(state['matrix']).values

    @property
    def matrix(self):
        return self._matrix

    @matrix.setter
    def matrix(self, new_matrix):
        self._matrix = new_matrix
        m11 = new_matrix[0][0]  # x scale
        m21 = new_matrix[0][1]  # x shear
        m31 = new_matrix[0][2]  # x translate

        m12 = new_matrix[1][0]  # y shear
        m22 = new_matrix[1][1]  # y scale
        m32 = new_matrix[1][2]  # y translate

        self.transform = QTransform(m11, m12, m21, m22, m31, m32)

        log.debug("m11={}, m12={}, m21={}, m22={}, m31={}, m32={}, matrix={}".format(m11, m12, m21, m22, m31, m32, QMatrix4x4(self.transform)))
        self.matrixChanged.emit()

    def __repr__(self):
        return "{}".format(self.matrix)
