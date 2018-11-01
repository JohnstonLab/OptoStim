import logging

import numpy as np
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QScrollArea, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QVBoxLayout

from pyjohnstonlab.gui.widgets.camera.cameracontrolswidget import CameraControlsWidget
from pyjohnstonlab.gui.widgets.camera.cameraframedisplaywidget import CameraFrameDisplayWidget

log = logging.getLogger(__name__)


class CameraWidget(QWidget):

    savePressed = pyqtSignal()

    def __init__(self, camera_device, workspace=None, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Camera Window')

        self._camera_device = camera_device
        self._workspace = workspace

        self.controls_widget = CameraControlsWidget()

        self.camera_frame_display = CameraFrameDisplayWidget()
        # self.camera_frame_display.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self.controls_widget)
        self.scroll_area.setMaximumWidth(500)

        layout = QHBoxLayout()
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.camera_frame_display)

        self.restart_acquisition_button = QPushButton("Restart Acquisition")
        self.snap_image_button = QPushButton("Save Image")
        self.stop_acquisition_button = QPushButton("Stop Acquisition")
        self.status_label = QLabel()
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        snap_image_layout = QHBoxLayout()
        snap_image_layout.addWidget(self.restart_acquisition_button)
        snap_image_layout.addWidget(self.stop_acquisition_button)
        snap_image_layout.addWidget(self.snap_image_button)
        snap_image_layout.addWidget(self.status_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(snap_image_layout)
        self.setLayout(main_layout)

        self.connect()

    def connect(self):
        self._camera_device.newFrameReceived.connect(self.show_cam_image)
        self.restart_acquisition_button.pressed.connect(lambda: self._camera_device.start_acquisition())
        self.snap_image_button.pressed.connect(self.on_save_image_button_pressed)
        self.stop_acquisition_button.pressed.connect(lambda: self._camera_device.stop_acquisition())

    def closeEvent(self, close_event):
        log.debug("Trying to stop acquisition")
        self._camera_device.stop_acquisition()
        log.debug("Trying to unload")
        self._camera_device.unload()

    @pyqtSlot(np.ndarray)
    def show_cam_image(self, image):
        self.camera_frame_display.image = image
        self.camera_frame_display.update()

    @pyqtSlot(float)
    def on_gainDoubleSpinBox_valueChanged(self, value):
        self._camera_device.gain = value

    def showEvent(self, show_event):

        self.controls_widget.update_controls(camera_device=self._camera_device)

    def on_save_image_button_pressed(self):
        self.savePressed.emit()

    def save_image(self, location, extension):
        if not self.camera_frame_display.image.save(location, extension):
            raise Exception("Could not save file to {}".format(location))

        self.status_label.setText("Image snapped {}".format(location))