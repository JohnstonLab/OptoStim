from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QHBoxLayout

from optostim.widgets.protocol_design.stimulus_point_pattern_widget import StimulusPointPatternWidget


class StimulusPointSetupWidget(QWidget):

    patternedChanged = pyqtSignal(bool)

    def __init__(self, stimulus_point, parent=None):
        super().__init__(parent)
        self.stimulus_point = stimulus_point

        self.check_box = QCheckBox(self)
        self.check_box.setText('{}'.format(stimulus_point.index))
        self.check_box.stateChanged.connect(self.on_check_box_stateChanged)

        self.pattern_widget = StimulusPointPatternWidget(self)
        self.pattern_widget.mouseDoubleClicked.connect(self.change_patterned)
        self.pattern_widget.hide()

        layout = QHBoxLayout()
        layout.addWidget(self.check_box)
        layout.addWidget(self.pattern_widget)

        self.setLayout(layout)

        self.patterned = False

    def is_checked(self):
        return self.check_box.isChecked()

    def on_check_box_stateChanged(self, state):
        self.pattern_widget.show() if state else self.pattern_widget.hide()

    def set_pattern_pixmap(self, pixmap):
        self.pattern_widget.label.setPixmap(pixmap)

    def change_patterned(self):
        self.patterned = not self.patterned
        self.patternedChanged.emit(self.patterned)

