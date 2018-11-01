import logging

from PyQt5.QtCore import QObject, pyqtSignal

from optostim.models.datamodels.protocol_element import ProtocolElementProperty

log = logging.getLogger(__name__)


class LabJackMapping(QObject):

    protocolElementPropertyChanged = pyqtSignal(ProtocolElementProperty, ProtocolElementProperty)

    def __init__(self, fio_number, protocol_element_property, parent=None):
        super().__init__(parent)
        self.fio = fio_number
        self._protocol_element_property = protocol_element_property

    @property
    def protocol_element_property(self):
        return self._protocol_element_property

    @protocol_element_property.setter
    def protocol_element_property(self, value):
        old_value = self.protocol_element_property
        self._protocol_element_property = value
        self.protocolElementPropertyChanged.emit(old_value, self._protocol_element_property)
        log.debug(value)