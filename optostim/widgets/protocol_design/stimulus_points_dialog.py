import logging
from math import sqrt
from random import sample

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog

from optostim.common import views
from pyjohnstonlab.mixins import LoadUIFileMixin
from optostim.models.datamodels.patterns.normal_pattern import NormalPattern
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint
from optostim.widgets.protocol_design.stimulus_point_setup_widget import StimulusPointSetupWidget

log = logging.getLogger(__name__)


class StimulusPointsDialog(QDialog, LoadUIFileMixin):

    stimulus_points_pattern_selected = pyqtSignal(list)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        uic.loadUi(views.get('StimulusPointsDialog.ui'), self)

        self.stimulus_point_setup_widgets = []
        self.make_radios()

        self.model.dataChanged.connect(lambda: self.make_radios())
        self.model.rowsRemoved.connect(lambda: self.make_radios())

        self._pattern = None

    def clear_selection(self):
        [radio.setCheckState(False) for radio in self.stimulus_point_setup_widgets]

    def make_radios(self):

        for widget in self.stimulus_point_setup_widgets:
            self.stimulusPointsGridLayout.removeWidget(widget)
            widget.deleteLater()

        self.stimulus_point_setup_widgets.clear()
        length = int(sqrt(self.model.rowCount()))

        row = 0
        column = 0

        for index, point in enumerate(self.model):
            radio = StimulusPointSetupWidget(point, self)
            radio.patternedChanged.connect(self.on_radio_patternChanged)
            radio.set_pattern_pixmap(NormalPattern.pixmap())
            radio.adjustSize()
            self.stimulus_point_setup_widgets.append(radio)
            self.stimulusPointsGridLayout.addWidget(radio, row, column)
            self.stimulusPointsGridLayout.setAlignment(radio, Qt.AlignCenter)

            column = column + 1 if column < length else 0
            row = row + 1 if column == 0 else row

      #  log.debug("Size is: {}".format(self.size()))
        #self.stimulusPointsGridLayout.adjustSize()
       # self.adjustSize()
        #self.setFixedSize(self.size())
      #  log.debug("make_radios. Size {}".format(self.size()))


    @pyqtSlot(bool)
    def on_radio_patternChanged(self, patterned):
        pixmap = self.pattern.pixmap() if patterned else NormalPattern.pixmap()
        self.sender().set_pattern_pixmap(pixmap)

    def random_stimulus_points(self, attempts):
        if len(self.stimulus_point_setup_widgets) == 0:
            return []

        indices = [i for i in range(len(self.stimulus_point_setup_widgets))]
        return sorted(sample(indices, attempts))

    def on_addStimulusPointsButton_pressed(self):
        selected_indices = self.selected_stimulus_points()
        self.clear_selection()

    def on_closeButton_pressed(self):
        self.close()

    @pyqtSlot()
    def on_deselectAllButton_pressed(self):
        for button in self.stimulus_point_setup_widgets:
            button.check_box.setChecked(False)

    @pyqtSlot()
    def on_selectAllButton_pressed(self):
        for button in self.stimulus_point_setup_widgets:
            button.check_box.setChecked(True)

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        self._pattern = value
        for widget in self.stimulus_point_setup_widgets:
            if widget.patterned:
                widget.set_pattern_pixmap(self._pattern.pixmap(16))

    def selected_stimulus_points(self):

        points_to_append = []

        for widget in self.stimulus_point_setup_widgets:
            if widget.is_checked():
                stimulus_point = widget.stimulus_point
                pattern = self.pattern if widget.patterned else NormalPattern
                points_to_append.append(SelectedStimulusPoint(stimulus_point=stimulus_point,
                                                              pattern=pattern))

        return points_to_append



