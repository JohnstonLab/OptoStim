import logging
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtWidgets import QWidget, QHeaderView, QAbstractItemView

from pyjohnstonlab.threading import execute_states_thread

log = logging.getLogger(__name__)


class LabJackWidget(QWidget):

    view_name = "LabJackView.ui"

    def __init__(self, labjack, labjack_states, parent=None):
        super().__init__(parent=parent)
        self.TableView = None
        self.labjack_device = labjack
        self.labjack_states = labjack_states
        self.is_executing = False
        self.setup_ui()
        self.connect()

    def connect(self):
        self.labjack_device.status_changed.connect(lambda text: self.labjackStatus.setText(text))

    def on_executeStatesButton_pressed(self):
        if self.is_executing:
            self.interrupt_execution()
        elif self.labjack_device.available():
            logging.debug('Starting execute states.')
            self.labjack_device.clear()
            count = int(self.ExecuteStatesLoopCount.value())
            delay = float(self.ExecuteStatesLoopDelay.value())

            self.thread = QThread()
            self.worker = execute_states_thread.ExecuteStatesWorker(number_of_times=count, delay=delay,
                                              device=self.labjack_device, states=self.labjack_states.states)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)

            self.worker.started.connect(self.on_execute_states_started)
            self.worker.loop_progress.connect(self.update_loop_progress)
            self.worker.finished.connect(self.on_execute_states_finished)
            self.worker.interrupted.connect(self.on_execute_states_finished)
            self.worker.finished.connect(self.thread.quit)

            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.finished.connect(self.worker.deleteLater)

            self.thread.start()

    def interrupt_execution(self):
        self.executeStatesButton.setText('Aborting...')
        self.thread.requestInterruption()

    def on_execute_states_finished(self):
        self.is_executing = False
        self.executeStatesButton.setText('Execute')
        self.labjack_device.clear()
        self.set_input_enabled(enabled=True)

    def on_execute_states_started(self):
        self.is_executing = True
        self.executeStatesButton.setText('Interrupt')
        self.set_input_enabled(enabled=False)
        self.LoopProgress.setValue(0)

    def update_loop_progress(self, value):
        self.LoopProgress.setValue(value * 100)
        logging.debug(value)

    def set_input_enabled(self, enabled):
        logging.debug('Input enabled: %i' % enabled)
        self.deleteStates.setEnabled(enabled)
        self.addStateButton.setEnabled(enabled)

    def setup_ui(self):
        p = Path(__file__).parents[1]
        view_location = p.joinpath('views/LabJackView.ui').__str__()

        uic.loadUi(view_location, self)

        self.TableView.setModel(self.labjack_states)

        self.TableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.TableView.resizeColumnsToContents()

        self.TableView.setAcceptDrops(True)
        self.TableView.setDragEnabled(True)
        self.TableView.setDefaultDropAction(Qt.MoveAction)
        self.TableView.setDragDropMode(QAbstractItemView.InternalMove)
        self.TableView.setDragDropOverwriteMode(False)
        self.TableView.setSelectionBehavior(QAbstractItemView.SelectRows)

        width = self.TableView.horizontalHeader().sizeHint().width() * self.TableView.horizontalHeader().count()
        self.TableView.setMinimumWidth(width)

        self.fio_states = [self.FIO4State, self.FIO5State, self.FIO6State, self.FIO7State]

        for fio in self.labjack_device.fios:
            getattr(self, "fio{}Label".format(fio.number)).setText(fio.label)

        getattr(self, "DAC0Label").setText(self.labjack_device.DAC0.label)
        getattr(self, "DAC1Label").setText(self.labjack_device.DAC1.label)

    def on_addStateButton_pressed(self):
        self.labjack_states.add_state(self.FIO4State.isChecked(), self.FIO5State.isChecked(), self.FIO6State.isChecked(),
                             self.FIO7State.isChecked(), self.DAC0Input.value(), self.DAC1Input.value(),
                             self.DurationInput.value())
        self.clear_new_input_state()

    def clear_new_input_state(self):
        [state.setChecked(False) for state in self.fio_states]
        self.DAC0Input.setValue(0.00)
        self.DAC1Input.setValue(0.00)
        self.DurationInput.setValue(0.00)

    def on_deleteStates_pressed(self):
        selection = self.TableView.selectionModel()
        model_indices = selection.selectedRows()
        [self.labjack_states.removeRow(model_index.row() - i) for i, model_index in enumerate(model_indices)]

    def on_section_moved(self, logical_index, old_visual_index, new_visual_index):
        self.model.move_state(old_visual_index, new_visual_index)