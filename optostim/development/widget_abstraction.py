import logging

from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QSpinBox, QLineEdit, QLabel, QDoubleSpinBox

log = logging.getLogger(__name__)

CONTROL_MAPPING = {
    QDoubleSpinBox: [QDoubleSpinBox.value, QDoubleSpinBox.setValue],
    QLabel:         [QLabel.text, QLabel.setText],
    QLineEdit:      [QLineEdit.text, QLineEdit.setText],
    QSpinBox:       [QSpinBox.value, QSpinBox.setValue]
}


class Control(QObject):

    valueChanged = pyqtSignal()

    def __init__(self, qt_control, initial_value=None):
        super().__init__()
        self.qt_control = qt_control
        self.getter = CONTROL_MAPPING[qt_control.__class__][0]
        self.setter = CONTROL_MAPPING[qt_control.__class__][1]

        if initial_value:
            self.value = initial_value

    def set_value(self, new_value):
        self.value = new_value

    @property
    def value(self):
        return self.setter(self.qt_control)

    @value.setter
    def value(self, new_value):
        self.setter(self.qt_control, new_value)
        self.valueChanged.emit()


def loadUI(path, base_instance=None):
    ui = uic.loadUi(path, base_instance)

    controls = []

    for key, value in ui.__dict__.items():
        klass = CONTROL_MAPPING.get(value.__class__, None)
        if klass:
            controls.append([key + '_control', Control(qt_control=value)])

    for control in controls:
        setattr(ui, control[0], control[1])

    return ui