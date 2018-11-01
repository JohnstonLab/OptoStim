from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDoubleSpinBox


class CameraExposureSpinBox(QDoubleSpinBox):

    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self._device = None
        self.device = device
        self.valueChanged.connect(self.on_valueChanged)

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, new_device):
        self._device = new_device
        if self.device:
            self._device.exposure_changed.connect(self.on_exposure_changed)

    @pyqtSlot(float)
    def on_exposure_changed(self, new_exposure):
        self.setValue(new_exposure)

    @pyqtSlot(float)
    def on_valueChanged(self, value):
        self._device.exposure = value

    def showEvent(self, *args, **kwargs):
        self.setValue(self.device.exposure)

