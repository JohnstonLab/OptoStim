import logging
import multiprocessing

import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
from multiprocessing import Process

from optostim.common import views
from pyjohnstonlab.decorators import mock_image
from pyjohnstonlab.devices.camera_device import GAIN, EXPOSURE

log = logging.getLogger(__name__)

MAX_SATURATED_PIXEL_ELEMENTS = 100


def fit_worker(meshgrid, data, out_queue):
    pass


class IntensityMaskSetupWidget(QWidget):

    def __init__(self, camera, intensity_mask, stimulus_widget, parent=None):
        super().__init__(parent)
        self._camera = camera
        self._intensity_mask = intensity_mask

        uic.loadUi(views.get('IntensityMaskSetup.ui'), self)

        self.current_index = 0
        self.gaussian_fit_queue = multiprocessing.Queue()
        self.gaussian_fit_process = None
        self.stimulus_widget = stimulus_widget

        self.gaussianFitPlot.add_navigation_toolbar()
        self.axes = self.gaussianFitPlot.figure.add_subplot(111)

#        self.background_colours = [self.stimulus_widget.full_brightness()]

        self.frame_numbers = np.zeros((MAX_SATURATED_PIXEL_ELEMENTS,))
        self.saturated_pixel_count = np.zeros((MAX_SATURATED_PIXEL_ELEMENTS,))

        self.setWindowTitle("Intensity Mask Setup")

        self.exposureSpinBox.device = camera
        self.gainSpinBox.device = camera

        self.exposureSpinBox.property_name = EXPOSURE

        self.connect()

    def connect(self):
        self._intensity_mask.fitChanged.connect(self.on_intensity_mask_fitChanged)
        self._intensity_mask.isFittingChanged.connect(self._on_intensity_mask_isFittingChanged)

    def closeEvent(self, event):
        self._camera.newFrameReceived.disconnect(self.on_camera_newFrameReceived)
        self._camera.stop_acquisition()

    def make_mask(self, offset):
        meshgrid = np.indices(self._intensity_mask.shape)
        mask = self._intensity_mask.gaussian_fit.func()(meshgrid[0], meshgrid[1])
        if offset > mask.max():
            offset = mask.max()
            log.info("Limiting offset to mask maximum ({})".format(offset))

        self.stimulus_widget.intensity_mask = np.minimum(1.0 - (mask - offset) / mask.max(), np.ones_like(mask))

    @pyqtSlot()
    def on_acquireMaskButton_pressed(self):
        image = self.cameraFrameDisplayWidget.ndarray
        self._intensity_mask.fit(image=image)

    @mock_image('development/image-2018-01-12_15-03-49.PNG')
    @pyqtSlot(np.ndarray)
    def on_camera_newFrameReceived(self, image):
        self.cameraFrameDisplayWidget.image = image
        saturated_pixels = np.sum(np.where(image >= 255.0))
        self.saturatedPixelCountLabel.setText("{}".format(saturated_pixels))

    @pyqtSlot(object)
    def on_intensity_mask_fitChanged(self, gaussian):
        self.amplitudeLabel.setText('{:0.2f}'.format(gaussian.amplitude))
        self.centreXLabel.setText('{:0.2f}'.format(gaussian.x0))
        self.centreYLabel.setText('{:0.2f}'.format(gaussian.y0))
        self.widthXLabel.setText('{:0.2f}'.format(gaussian.width_x))
        self.widthYLabel.setText('{:0.2f}'.format(gaussian.width_y))
        self.rotationLabel.setText('{:0.2f}'.format(gaussian.rotation))

        if self._intensity_mask.is_set:
            self.gaussianFitPlot.figure.clear()
            ax = self.gaussianFitPlot.figure.add_subplot(111)
            if self._intensity_mask.source is not None:
                ax.imshow(self._intensity_mask.source, cmap='gray', clim=(0.0, 255.0))
            meshgrid = np.indices(self._intensity_mask.shape)
            mask = gaussian.func()(meshgrid[0], meshgrid[1])
            ax.contour(mask, 10, colors='r')
            self.gaussianFitPlot.canvas.draw()
            self.make_mask(offset=self.maskOffsetSpinBox.value())

    @pyqtSlot(int)
    def on_maskOffsetSpinBox_valueChanged(self, value):
        try:
            self.make_mask(offset=value)
        except ValueError:
            pass

    @pyqtSlot(int)
    def on_stimulusWindowBackgroundSpinBox_valueChanged(self, value):
        self.stimulus_widget.background_colour = value

    def on_invertStimulusWindowBackground_stateChanged(self, state):
        self.stimulus_widget.inverted = state

    def showEvent(self, event):
        self._camera.newFrameReceived.connect(self.on_camera_newFrameReceived)
        self._camera.start_acquisition()

    @pyqtSlot(bool)
    def _on_intensity_mask_isFittingChanged(self, state):
        self.acquireMaskButton.setEnabled(not state)


