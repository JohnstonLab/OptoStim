import pathlib

import matplotlib.image as mpimg
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

from optostim.common import paths
from optostim.common.tiff_reader import read_tif
from optostim.exceptions import OptoStimException

DEFAULT_FOV_AT_ZOOM_1 = 910


class ImageStack(QObject):

    dataChanged = pyqtSignal()
    filenameChanged = pyqtSignal(str)
    fovChanged = pyqtSignal(float)
    zoomChanged = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.headers = None
        self.data = None
        self.descriptions = None
        self.dimensions = None
        self.median = 0
        self.max = 0
        self._filename = ''
        self.file = ''
        self._zoom = 0.0
        self._fov = 0.0

        self.fov_at_zoom_1 = DEFAULT_FOV_AT_ZOOM_1

    def __getstate__(self):
        return {'filename': self.filename}

    def __setstate__(self, state):
        self.filename = state['filename']

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, new_file):
        if self.filename != new_file:
            self._filename = new_file
            self._read_in_image(self.filename)

    @property
    def fov(self):
        return self._fov

    @fov.setter
    def fov(self, new_fov):
        if self._fov != new_fov:
            self._fov = new_fov
            self.fovChanged.emit(self._fov)

    @property
    def height(self):
        return 0 if self.data is None else self.data.shape[self.data.ndim - 2]

    def set_data(self, filename, headers, data, descriptions):
        self.headers = headers
        self.data = data
        self.descriptions = descriptions
        self.dimensions = data.shape
        self.median = np.median(data, 0)
        self.max = np.max(data, 0)
        self.filename = filename
        self.file = paths.basename(filename)

        try:
            self.zoom = float(headers['SI.hRoiManager.scanZoomFactor'])
        except (KeyError, TypeError):
            self.zoom = 1.0
            self.fov = DEFAULT_FOV_AT_ZOOM_1
        else:
            self.fov = DEFAULT_FOV_AT_ZOOM_1 / self.zoom

        self.dataChanged.emit()

    def set_fov_at_zoom_1(self, new_value):
        self.fov_at_zoom_1 = new_value
        self.fov = self.fov_at_zoom_1 / self.zoom

    @property
    def zoom(self):
        return self._zoom

    @property
    def width(self):
        return 0 if self.data is None else self.data.shape[self.data.ndim - 2]

    @zoom.setter
    def zoom(self, new_zoom):
        self._zoom = new_zoom
        self.zoomChanged.emit(new_zoom)

    def _read_in_image(self, filename):
        extension = pathlib.Path(filename).suffix
        metadata = None
        descriptions = None

        if extension == '.tif':
            try:
                metadata, data, descriptions = read_tif(filename)
            except ValueError as e:
                raise OptoStimException(e)
        else:
            data = mpimg.imread(filename)

        self.set_data(filename, metadata, data, descriptions)