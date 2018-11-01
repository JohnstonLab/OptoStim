import logging

from pyjohnstonlab.devices.exceptions import DeviceException
from pyjohnstonlab.gui.widgets.execute_loop_widget import ExecuteLoopWidget
from pyjohnstonlab.gui import message_boxes
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget

from optostim.common import views
from pyjohnstonlab.mixins import LoadUIFileMixin
from optostim.models.datamodels.patterns.increment_by_one_pattern import IncrementByOnePattern
from optostim.models.datamodels.patterns.normal_pattern import NormalPattern
from optostim.models.datamodels.patterns.random_pattern import RandomPattern
from optostim.models.datamodels.program import Program
from optostim.models.datamodels.selected_stimulus_point import SelectedStimulusPoint
from optostim.models.itemmodels.protocol_sequence import ProtocolSequence
from optostim.threads.execute_protocol_sequence_worker import ExecuteProtocolSequenceWorker
from optostim.widgets.program_scroll_area_widget import ProgramScrollAreaWidget
from optostim.widgets.protocol_design.stimulus_points_dialog import StimulusPointsDialog

log = logging.getLogger(__name__)


class ProtocolDesignWidget(QWidget, LoadUIFileMixin):

    # todo - temp to let other parts of program know when protocol running. Program object itself should reside
    #         inside main window.
    programStarted = pyqtSignal()

    def __init__(self, image_stack, intensity_mask, labjack,
                 stimulus_points, selected_stimulus_points, stimulus_widget, workspace, parent=None):
        super().__init__(parent)
        # self.fio_mappings = fio_mappings
        self.image_stack = image_stack
        self._intensity_mask = intensity_mask
        self.labjack = labjack
        self.program = None
        self.protocol_sequence = selected_stimulus_points
        self.stimulus_points = stimulus_points
        self.stimulus_points_dialog = None
        self.stimulus_sequence_thread = None
        self.stimulus_sequence_worker = None
        self.stimulus_widget = stimulus_widget
        self.workspace = workspace

        uic.loadUi(views.get('ProtocolDesignView.ui'), self)

        self.stimulus_points_dialog = StimulusPointsDialog(model=self.stimulus_points, parent=self)

        self.execute_loop_widget = ExecuteLoopWidget(parent=self)
        self.inputLayout.addWidget(self.execute_loop_widget)

        self.program_scroll_area_widget = ProgramScrollAreaWidget(self)

        self.program_scroll_area_widget.set_model(self.protocol_sequence)
        self.programScrollArea.setWidget(self.program_scroll_area_widget)

        self.chooseFromInput.setRange(0, 0)

        self.patterns = [IncrementByOnePattern, RandomPattern]

        self.pattern_icons = []

        for pattern in self.patterns:
            self.patternComboBox.insertItem(self.patternComboBox.count(), pattern.icon(), pattern.name, pattern)

        self.fio4Mapping.setText(self.labjack.fio4.label)
        self.fio5Mapping.setText(self.labjack.fio5.label)
        self.fio6Mapping.setText(self.labjack.fio6.label)
        self.fio7Mapping.setText(self.labjack.fio7.label)

        self.protocol_sequence.random_seed = self.randomSeedSpinBox.value()

        self.connect()

    def connect(self):

        self.execute_loop_widget.loop.valueChanged.connect(self.on_ExecuteLoopValue_valueChanged)
        self.execute_loop_widget.execute.pressed.connect(self.on_execute)

        self.laserInput.toggled.connect(lambda checked: self.waitInput.setChecked(False) if checked else None)
        self.pmtInput.toggled.connect(lambda checked: self.waitInput.setChecked(False) if checked else None)
        self.syncInput.toggled.connect(lambda checked: self.waitInput.setChecked(False) if checked else None)

        self.labjack.fio4.labelChanged.connect(lambda text: self.fio4Mapping.setText(text))
        self.labjack.fio5.labelChanged.connect(lambda text: self.fio5Mapping.setText(text))
        self.labjack.fio6.labelChanged.connect(lambda text: self.fio6Mapping.setText(text))
        self.labjack.fio7.labelChanged.connect(lambda text: self.fio7Mapping.setText(text))

        self.protocol_sequence.randomSeedChanged.connect(lambda new_seed: self.randomSeedSpinBox.setValue(new_seed))

        self.stimulus_points_dialog.stimulus_points_pattern_selected.connect(self.add_stimulus_point_list)

        self.stimulus_points.dataChanged.connect(lambda: self.chooseFromInput.setRange(1, self.stimulus_points.rowCount()))
        self.stimulus_points.rowsRemoved.connect(lambda: self.on_clearListButton_pressed())

        self.workspace.dataLoaded.connect(self.on_workspace_dataLoaded)

    def add_stimulus_point_list(self, stimulus_points_indices):

        if not stimulus_points_indices:
            return

        last_row = self.protocol_sequence.rowCount()

        selected_stimulus_points = [self.stimulus_points.points[i] for i in stimulus_points_indices]

        if self.protocol_sequence.insertRow(self.protocol_sequence.rowCount()):
            model_index = self.protocol_sequence.index(last_row, 0)
            self.protocol_sequence.setData(model_index, value=selected_stimulus_points, role=Qt.EditRole)

    def clear_inputs(self):
        self.laserInput.setChecked(False)
        self.pmtInput.setChecked(False)
        self.syncInput.setChecked(False)
        self.waitInput.setChecked(False)
        self.durationInput.setValue(0.0)

    @pyqtSlot()
    def on_addProtocolElementButton_pressed(self):

        laser = self.get_input('laser')
        pmt = self.get_input('pmt')
        sync = self.get_input('sync')
        wait = self.get_input('wait')
        duration = self.get_input('duration')

        self.protocol_sequence.add_element(self.select_stimulus_points(), laser, pmt, sync, wait, duration)
        loop_count = self.execute_loop_widget.loop.value()
        self.update_generated_sequence_views(loop_count=loop_count)
        self.clear_inputs()

    @pyqtSlot()
    def on_execute(self):
        if len(self.protocol_sequence) == 0:
            message_boxes.warning(self, title="Empty Protocol!", text="No elements have been added to the protocol!")
            return

        if self.stimulus_sequence_thread and self.stimulus_sequence_thread.isRunning():
            if self.stimulus_sequence_thread.isInterruptionRequested():
                return
            if message_boxes.question(self, title="Busy", text="Program is still executing, would you like to abort?"):
                self.stimulus_sequence_thread.requestInterruption()
                self.execute_loop_widget.execute.setText('Aborting')
            return

        problems = []

        if not self.stimulus_widget.isVisible():
            problems.append("Stimulus window is not visible.")

        if not self.labjack.is_connected:
            problems.append("LabJack not found.")

        if problems:
            text = "The following problems were found:\n\n"
            for problem in problems:
                text += problem + "\n"
            text += "\nWould you like to continue?"
            if not message_boxes.question(self, "Problems Found", text):
                return

        if self.labjack.is_connected:
            self.labjack.clear()

        self.stimulus_sequence_thread = QThread()
        self.stimulus_sequence_thread.setObjectName('Program Thread')

        # if self.stimulus_widget.isVisible():
        #     self.program.generate_image_set()

        self.stimulus_sequence_worker = ExecuteProtocolSequenceWorker(program=self.program, labjack=self.labjack)
        self.stimulus_sequence_worker.moveToThread(self.stimulus_sequence_thread)

        self.stimulus_sequence_worker. \
            elementChanged.connect(lambda points: self.stimulus_widget.scene().display_points(points))
        self.stimulus_sequence_worker.loop_progress.connect(self.execute_loop_widget.update_progress_bar)

        self.stimulus_sequence_worker.interrupted.connect(self.stimulus_sequence_thread.quit)

        self.stimulus_sequence_worker.finished.connect(self.on_stimulus_sequence_finished)
        self.stimulus_sequence_worker.finished.connect(self.stimulus_sequence_thread.quit)

        if self.labjack.is_connected:
            self.stimulus_sequence_worker.finished.connect(lambda: self.labjack.clear())

        self.stimulus_sequence_thread.started.connect(self.on_thread_start)
        self.stimulus_sequence_thread.started.connect(self.stimulus_sequence_worker.run)

        self.stimulus_sequence_thread.finished.connect(self.on_thread_stop)
        self.stimulus_sequence_thread.finished.connect(self.stimulus_sequence_worker.deleteLater)

        self.stimulus_sequence_thread.start()
        self.programStarted.emit()

    # @pyqtSlot()
    # def on_abort_complete(self):
    #     self.on_t

    @pyqtSlot()
    def on_thread_start(self):
        self.labjack.check_device = False
        self.execute_loop_widget.execute.setText('Abort')

    @pyqtSlot()
    def on_thread_stop(self):
        self.labjack.check_device = True
        try:
            self.labjack.clear()
        except DeviceException:
            pass

        self.stimulus_widget.image = None
        self.execute_loop_widget.execute.setText('Execute')

    @pyqtSlot(int)
    def on_patternComboBox_currentIndexChanged(self, index):
        self.stimulus_points_dialog.pattern = self.pattern()
        self.update_generated_sequence_views(pattern=self.pattern(), loop_count=self.execute_loop_widget.loop.value())

    @pyqtSlot(str)
    def on_workspace_dataLoaded(self, loaded_from):
        for e in self.protocol_sequence.loaded_in_protocol['protocol']:
            stimulus_points = []

            for point in e['stimulus_points']:
                stimulus_point = self.stimulus_points[point['stimulus_point_index']]
                stimulus_points.append(SelectedStimulusPoint(stimulus_point=stimulus_point, pattern=point['pattern']))

            self.protocol_sequence.add_element(stimulus_points=stimulus_points, laser=e['laser'], pmt=e['pmt'],
                                               sync=e['sync'], wait=e['wait'], duration=e['duration'])
        self.protocol_sequence.pattern = self.protocol_sequence.loaded_in_protocol['pattern']
        self.patternComboBox.setCurrentIndex(self.patternComboBox.findText(self.protocol_sequence.pattern.name))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selection = self.stimulus_points.selectionModel()
            model_indices = selection.selectedRows()
            [self.protocol_sequence.removeRow(model_index.row() - i) for i, model_index in enumerate(model_indices)]
        else:
            super().keyPressEvent(event)

    @pyqtSlot(int)
    def on_ExecuteLoopValue_valueChanged(self, value):
        self.update_generated_sequence_views(loop_count=value)

    @pyqtSlot(int)
    def on_patternComboBox_currentIndexChanged(self, index):
        pattern = self.patternComboBox.currentData()
        self.stimulus_points_dialog.pattern = pattern
        self.protocol_sequence.pattern = pattern
        self.update_generated_sequence_views()

    @pyqtSlot(int, int)
    def on_protocol_elementChanged(self, loop, iteration):
        self.stimulus_widget.image = self.program.get_image(loop, iteration)

    @pyqtSlot()
    def on_selectStimulusPointsButton_pressed(self):
        self.stimulus_points_dialog.show()

    @pyqtSlot(int)
    def on_randomInput_stateChanged(self, state):
        self.chooseFromInput.setEnabled(state)

    @pyqtSlot(int)
    def on_randomSeedSpinBox_valueChanged(self, value):
        self.protocol_sequence.random_seed = value

    @pyqtSlot()
    def on_stimulus_sequence_finished(self):
        self.stimulus_widget.image = None

    @pyqtSlot(bool)
    def on_waitInput_toggled(self, checked):
        if checked:
            self.laserInput.setChecked(False)
            self.pmtInput.setChecked(False)
            self.syncInput.setChecked(False)
            self.durationInput.setValue(0.00)

    @pyqtSlot()
    def on_clearListButton_pressed(self):
        self.protocol_sequence.removeRows(0, self.protocol_sequence.rowCount())
        self.update_generated_sequence_views(loop_count=0)
        self.stimulus_widget.scene().display_points([])

    def pattern(self):
        return self.patternComboBox.currentData()

    @pyqtSlot()
    def on_sendPreviewButton_pressed(self):
        iteration = self.iterationPreviewSpinBox.value()
        loop = self.loopNumberPreviewSpinBox.value()
        self.stimulus_widget.open()
        self.stimulus_widget.scene().display_points([p.stimulus_point for p in self.program[loop][iteration].stimulus_points])

    def select_stimulus_points(self):
        selected_stimulus_points = []

        if self.randomInput.isChecked():
            chosen_points = self.stimulus_points.sample(choose=self.chooseFromInput.value())
            selected_stimulus_points = [
                SelectedStimulusPoint(stimulus_point=point, pattern=NormalPattern)
                for point in chosen_points
            ]
        elif self.stimulus_points_dialog:
            selected_stimulus_points = self.stimulus_points_dialog.selected_stimulus_points()

        return selected_stimulus_points

    def update_generated_sequence_views(self, loop_count=None):
        if not loop_count:
            loop_count = self.execute_loop_widget.loop.value()
        # todo - don't remake this every time, fix and move to main window and generate sequence in place
        if self.protocol_sequence.protocol:
            self.program = Program(image_stack=self.image_stack,
                                   initial_sequence=self.protocol_sequence.protocol,
                                   inter_loop_delay=self.execute_loop_widget.loop_delay.value(),
                                   random_seed=self.protocol_sequence.random_seed,
                                   stimulus_points=self.stimulus_points,
                                   stimulus_widget=self.stimulus_widget,
                                   pattern=self.protocol_sequence.pattern,
                                   loop_count=loop_count)
            self.program.generate()
            models = [ProtocolSequence(sequence=sequence) for sequence in self.program.program]
            self.program_scroll_area_widget.set_number_of_widgets(models=models, number=loop_count)
