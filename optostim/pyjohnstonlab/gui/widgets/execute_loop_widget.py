import os
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget


import logging
log = logging.getLogger(__name__)


class ExecuteLoopWidget(QWidget):

    # aborted = pyqtSignal()
    # execute = pyqtSignal(int, float)
    # loop_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        view = os.path.join(os.path.dirname(__file__), os.pardir, 'views', 'ExecuteLoopView.ui')
        uic.loadUi(view, self)
        self.execute = self.executeButton
        self.loop = self.loopSpinBox
        self.loop_delay = self.loopDelaySpinBox
        self.progress = self.progressBar


    # @property
    # def loop(self):
    #     return self.loopSpinBox.value()
    #
    # @loop.setter
    # def loop(self, value):
    #     self.loopSpinBoxValue.setValue(value)

        # self.loopCount.valueChanged.connect(self.on_loopCount_change)

    # def loop_count(self):
    #     return self.loopCount.value()
    #
    # @pyqtSlot(int)
    # def on_loopCount_change(self, value):
    #     self.loop_count_changed.emit(value)
    #
    # def abort_complete(self):
    #     self._executing = False
    #     self.executeButton.setText("Execute")
    #     self.update_progress_bar(value=0)
    #     self.executeButton.setEnabled(True)
    #
    # def _execute(self):
    #     self.executeButton.setText("Abort")
    #     self.execute.emit(self.loopCount.value(), self.ild.value())
    #     self.update_progress_bar(0)
    #     self._executing = True
    #
    # def _finished(self):
    #     self.executeButton.setText("Execute")
    #     self.executeButton.setEnabled(True)
    #     self._executing = False
    #
    # def on_executeButton_pressed(self):
    #     if self._executing:
    #         self._try_abort()
    #     else:
    #         self._execute()
    #
    # def _try_abort(self):
    #     self.aborted.emit()
    #     self.executeButton.setEnabled(False)
    #     self.executeButton.setText('Aborting')

    def update_progress_bar(self, value, max_value=100):
        self.progressBar.setValue(value * 100)



