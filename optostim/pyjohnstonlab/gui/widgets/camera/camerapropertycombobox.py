from PyQt5.QtWidgets import QComboBox


class CameraPropertyComboBox(QComboBox):
    def __init__(self, camera_device, camera_property, parent=None):
        super().__init__(parent)
        self.camera_property = camera_property
        self._device = camera_device
        self.addItems(camera_property.allowed_values)
        self.currentTextChanged.connect(self.on_currentTextChanged)

    def on_currentTextChanged(self, new_value):
        self._device.set_property(name=self.camera_property.name, value=new_value)
