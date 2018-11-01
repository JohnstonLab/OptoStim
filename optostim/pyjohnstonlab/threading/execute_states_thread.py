import logging
from time import sleep

from PyQt5.QtCore import QThread

from pyjohnstonlab.threading.thread_worker import ThreadWorker

log = logging.getLogger(__name__)


class ExecuteStatesWorker(ThreadWorker):

    def __init__(self, number_of_times, delay, device, states):
        super().__init__()
        self.number_of_times = number_of_times
        self.delay = delay
        self.device = device
        self.states = states

    def can_run(self):
        return (self.number_of_times > 0) and self.device

    def do_work(self):
        command_lists = self.device.generate_command_lists(self.states)
        current_thread = QThread.currentThread()
        # 16khz clock

        # Note checking if thread has interruption could be expensive and add time. Test in future to know
        # potential issues

        for loop_iter in range(self.number_of_times):
            for i in range(len(command_lists)):
                self.device.execute_command_list(command_lists[i])
                sleep(self.states[i][6])

            sleep(self.delay)
            self.loop_progress.emit((loop_iter + 1) / self.number_of_times)
            if current_thread.isInterruptionRequested():
                return False

        return True








