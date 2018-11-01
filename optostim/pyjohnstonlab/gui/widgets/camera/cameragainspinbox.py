from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDoubleSpinBox


class CameraGainSpinBox(QDoubleSpinBox):

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
        if new_device:
            self._device.gainChanged.connect(self.on_gainChanged)

    @pyqtSlot(float)
    def on_gainChanged(self, new_gain):
        self.setValue(new_gain)

    @pyqtSlot(float)
    def on_valueChanged(self, value):
        self._device.gain = value

    def showEvent(self, event):
        self.setValue(self.device.gain)

