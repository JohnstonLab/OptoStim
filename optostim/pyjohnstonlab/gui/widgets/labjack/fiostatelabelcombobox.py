from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QComboBox


class FioStateLabelComboBox(QComboBox):

    def __init__(self, parent):
        super().__init__(parent)
        self._labjack = None
        self._fio_state = None

    @property
    def fio_state(self):
        return self._fio_state

    @fio_state.setter
    def fio_state(self, new_fio_state):
        self._fio_state = new_fio_state
        self._fio_state.labelChanged.connect(lambda text: self.setCurrentText(text))

    @property
    def labjack(self):
        return self._labjack

    @labjack.setter
    def labjack(self, labjack):
        self._labjack = labjack
        for i, fio_state in enumerate(self._labjack.fios):

            self.insertItem(i, fio_state.label, fio_state)

    @pyqtSlot(str)
    def on_currentTextChanged(self, text):
        for state in self._labjack.fios:
            if state.label == text and state != self:
                state.label = self.fio_state.label
                break

        self.fio_state.label = text

    def set(self, labjack, fio):
        self.fio_state = fio
        self.labjack = labjack
        self.setCurrentIndex(self.findText(self.fio_state.label))
        self.currentTextChanged.connect(self.on_currentTextChanged)





