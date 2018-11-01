import logging
import os

import datetime
import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QDir
from PyQt5.QtWidgets import QWidget

from optostim.common.paths import Paths

log = logging.getLogger(__name__)


class CameraWindow(QWidget):

    def __init__(self, camera_device, workspace, parent=None):
        super().__init__(parent=parent)
        self.camera = camera_device
        self.workspace = workspace

        self.setWindowTitle('Camera Window')

        current_directory = os.path.dirname(__file__)
        relative_location = '../views/CameraWindowView.ui'
        path = os.path.join(current_directory, relative_location)
        uic.loadUi(path,  self)

    def closeEvent(self, close_event):
        log.debug("Trying to stop acquisition")
        self.camera.newFrameReceived.disconnect(self.on_camera_newFrameReceived)
        self.camera.stop_acquisition()

    @pyqtSlot(np.ndarray)
    def on_camera_newFrameReceived(self, image):
        self.cameraFrameDisplay.image = image

    @pyqtSlot()
    def on_saveImageButton_pressed(self):
        extension = "PNG"
        filename = "image-{:%Y-%m-%d_%H-%M-%S}.{}".format(datetime.datetime.now(), extension)

        location = Paths.join(self.workspace.working_directory, Paths.camera_images)

        location_directory = QDir(location)

        if not location_directory.exists():
            if not location_directory.mkdir(location):
                raise Exception("Could not create path {} to save image.".format(location))

        full_path = Paths.join(location, filename)

        if not self.cameraFrameDisplay.image.save(full_path, extension):
                raise Exception("Could not save file to {}".format(full_path))

        self.statusLabel.setText("Image snapped {}".format(full_path))

    def showEvent(self, show_event):
        self.camera.newFrameReceived.connect(self.on_camera_newFrameReceived)
        self.cameraControlsWidget.controls_widget.update_controls(camera_device=self.camera)
        self.camera.start_acquisition()
