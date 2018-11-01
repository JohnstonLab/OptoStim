import numpy as np
from PyQt5.QtGui import QImage


def ndarray_to_qimage(array, format):
    if not isinstance(array, np.ndarray):
        raise ValueError("Array must be of ndarray type.")
    height, width = array.shape
    return QImage(array.data, width, height, array.strides[0], format)