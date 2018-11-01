import logging
from time import sleep

from PyQt5.QtCore import pyqtSignal, QThread

from optostim.models.datamodels.labjack_state_model import LabJackStateModel
from pyjohnstonlab.threading.thread_worker import ThreadWorker

log = logging.getLogger(__name__)


class ExecuteProtocolSequenceWorker(ThreadWorker):

    # todo - create stimulus window on thread to avoid signals perhaps - better performance if latency important?

    # todo - concurrency for sleeps to allow thread event loop to process, can abort then almost instantly

    active_stimuli_points_changed = pyqtSignal(list, float)

    elementChanged = pyqtSignal(list)

    def __init__(self, labjack, program):
        super().__init__()
        self.labjack = labjack
        #  todo do not use string here for wait. Enum! Just quick fix :(
        self.wait_fio_number = next((fio.number for fio in self.labjack.fios if fio.label == 'Wait'))
        self.program = program

    def _do_protocol_sequence(self, i, command_lists):
        for ii, sequence_element in enumerate(self.program[i]):
            #self.program.stimulus_widget.scene().display_points([p.stimulus_point for p in sequence_element.stimulus_points])
           # self.elementChanged.emit(i, ii)
            self.elementChanged.emit([p.stimulus_point for p in sequence_element.stimulus_points])
            if command_lists[ii]:
                self.labjack.execute_command_list(command_lists[ii])
            if sequence_element.wait:
                self.labjack.wait_for_signal(io_number=self.wait_fio_number)
            else:
                sleep(sequence_element.duration)

    def do_work(self):

        # todo temp quick ugly fix
        labels = ['Laser', 'PMT', 'Sync', 'Wait', 'Duration']

        current_thread = QThread.currentThread()
        labjack_states = []
        for seq in self.program.initial_sequence:
            # todo ugly temp fix related to above
            fio4 = seq[1 + labels.index(list(filter(lambda x: x.number == 4, self.labjack.fios))[0].label)]
            fio5 = seq[1 + labels.index(list(filter(lambda x: x.number == 5, self.labjack.fios))[0].label)]
            fio6 = seq[1 + labels.index(list(filter(lambda x: x.number == 6, self.labjack.fios))[0].label)]
            fio7 = seq[1 + labels.index(list(filter(lambda x: x.number == 7, self.labjack.fios))[0].label)]
            labjack_states.append(LabJackStateModel(fio4state=fio4, fio5state=fio5, fio6state=fio6, fio7state=fio7,
                                                    duration=seq.duration))
        if self.labjack.is_connected:
            command_lists = self.labjack.generate_command_lists(states=labjack_states)
        else:
            command_lists = len(labjack_states) * [[]]
        program_loops = len(self.program)

        for i in range(program_loops):
            self._do_protocol_sequence(i, command_lists)
            if current_thread.isInterruptionRequested():
                return False
            else:
                sleep(self.program.ild)
                self.loop_progress.emit((i + 1) / program_loops)
        self.program.stimulus_widget.scene().display_points([])
        return True


