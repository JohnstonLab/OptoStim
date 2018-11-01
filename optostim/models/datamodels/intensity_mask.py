import logging
import multiprocessing

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from pyjohnstonlab.curves import Gaussian, fitgaussian

log = logging.getLogger(__name__)

FIT_PROCESS_CHECK_INTERVAL = 500


class IntensityMask(QObject):

    applyChanged = pyqtSignal(bool)
    isFittingChanged = pyqtSignal(bool)
    fitChanged = pyqtSignal(object)
    isSetChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply = False
        self._fit_process_complete_timer = QTimer(parent=self)
        self._fit_process_complete_timer.timeout.connect(self._check_fit_task)
        self._fit_process_complete_timer.setInterval(FIT_PROCESS_CHECK_INTERVAL)
        self._fit_task_result = None
        self._gaussian_fit = Gaussian()
        self._is_fitting = False
        self._is_set = False
        self._source = None
        self._shape = (0, 0)
        self._pool = None

    def __getstate__(self):
        return {
            'gaussian_fit': self.gaussian_fit,
            'shape': self.shape
        }

    def __setstate__(self, state):
        self._shape = state['shape']
        self.gaussian_fit = state['gaussian_fit']

    @property
    def apply(self):
        return self._apply

    @apply.setter
    def apply(self, value):
        self._apply = value
        self.applyChanged.emit(self._apply)

    def apply_to_image(self, image):
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be of numpy array type.")
        masked_image = image.copy()
        if self.is_set:
            if self.apply:
                scale_x = image.shape[1] / self._source.shape[1]
                scale_y = image.shape[0] / self._source.shape[0]
                meshgrid = np.indices(image.shape)
                gaussian = self._gaussian_fit.func(scale_x, scale_y)(meshgrid[1], meshgrid[0])
                masked_image = image.astype(np.float64) * (1.0 - gaussian / gaussian.max())
        else:
            log.warning("Intensity mask is not set. Can not apply.")
        log.debug("Dtype: {}".format(masked_image.dtype))
        return masked_image.astype(np.uint8)

    def fit(self, image):
        if not self.is_fitting:
            self._fit(image=image)
        else:
            log.warning("A fit is already in progress")

    @property
    def gaussian_fit(self):
        return self._gaussian_fit

    @gaussian_fit.setter
    def gaussian_fit(self, new_fit):
        self._gaussian_fit = new_fit
        self._is_set = True
        self.isSetChanged.emit(self._is_set)
        self.fitChanged.emit(self.gaussian_fit)

    @property
    def is_fitting(self):
        return self._is_fitting

    @property
    def is_set(self):
        return self.shape != (0, 0)

    @property
    def mask(self):
        return self._mask

    def on_gaussianFitWorker_parametersReady(self, *args, **kwargs):
        self.gaussian_fit.parameters = args[0]
        self._is_set = True
        self.isSetChanged.emit(self._is_set)
        self.fitChanged.emit(self.gaussian_fit)

    @property
    def shape(self):
        return self._shape

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, new_image):
        self._source = new_image

    def _check_fit_task(self):
        try:
            if self._fit_task_result.ready():
                self._fit_process_complete_timer.stop()
                self._pool.close()
                self._pool.join()
                self._is_fitting = False
                self.isFittingChanged.emit(self._is_fitting)
        except AttributeError:
            pass

    def _fit(self, image):
        self._is_fitting = True
        self.isFittingChanged.emit(self._is_fitting)
        self.source = image
        self._shape = image.shape
        self._pool = multiprocessing.Pool(processes=1)
        self._fit_process_complete_timer.start()
        self._fit_task_result = self._pool.apply_async(func=fitgaussian,
                                                       args=(image.astype(np.float64),),
                                                       callback=self.on_gaussianFitWorker_parametersReady)


