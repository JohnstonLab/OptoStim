import logging

from PyQt5.QtWidgets import QRadioButton

log = logging.getLogger(__name__)


class FIOStateRadioButton(QRadioButton):

    def __init__(self, parent):
        super().__init__(parent)
        self.setAutoExclusive(False)
        self._labjack = None
        self.toggled.connect(self.on_toggled)
        self._fio_number = 0

    def on_toggled(self, state):
        if self._labjack.is_connected:
            if self._fio_number > 0:
                self._labjack.set_fio_state(self._fio_number, state)
        else:
            log.warning("LabJack not connected. Can not set FIO state {}.".format(self._fio_number))

    def set(self, labjack, fio_num):
        self._labjack = labjack
        self._fio_number = fio_num
