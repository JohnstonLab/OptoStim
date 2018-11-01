import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDoubleSpinBox

from pyjohnstonlab.devices.camera_device import CameraProperty

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

SPIN_BOX_MAX = 1000


class CameraPropertyDoubleSpinBox(QDoubleSpinBox):

    def __init__(self, parent, camera_device=None, camera_property=None):
        super().__init__(parent)
        self._camera_property = camera_property
        if self._camera_property:
            self._update_limits()
            self.setValue(camera_property.current)
        self._device = camera_device
        self.property_name = ''
        self.valueChanged.connect(self.on_valueChanged)

    @property
    def camera_property(self):
        return self._camera_property

    @camera_property.setter
    def camera_property(self, new_property):
        if not isinstance(new_property, CameraProperty):
            raise ValueError("Property must be an instance of {} instead of {}".format(CameraProperty, new_property.__class__))
        self._camera_property = new_property
        self._update_limits()

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, new_device):
        self._device = new_device
        self._device.initialised.connect(self.on_device_initialised)

    def on_device_initialised(self):
        if self.property_name:
            try:
                prop = self.device.properties_dict[self.property_name]
            except KeyError as e:
                log.warning("Device does not have property: {}".format(e))
            else:
                self.camera_property = prop

    @pyqtSlot(float)
    def on_valueChanged(self, new_value):
        if self.device:
            if self.camera_property:
                self.device.set_property(name=self.camera_property.name, value=new_value)
            else:
                log.warning("Camera property not set on {}".format(self.__class__))
        else:
            log.warning("Camera device not set for property {}".format(self.camera_property))

    def showEvent(self, event):
        try:
            value = float(self.device.get_property(self.camera_property.name))
        except AttributeError:
            pass
        except ValueError:
            self.setValue(0.0)
        else:
            self.setValue(value)

    def _update_limits(self):
        if self._camera_property.has_limits:
            self.setRange(self._camera_property.min, self._camera_property.max)
        else:
            self.setRange(0, SPIN_BOX_MAX)