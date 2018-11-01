from PyQt5.QtCore import QObject, pyqtSignal

import logging
log = logging.getLogger(__name__)


class ThreadWorker(QObject):

    loop_progress = pyqtSignal(float)
    started = pyqtSignal()
    finished = pyqtSignal()
    interrupted = pyqtSignal()

    def run(self):
        log.debug('Starting thread')
        self.started.emit()
        if self.do_work():
            self.finished.emit()
        else:
            self.interrupted.emit()

    def do_work(self):
        raise NotImplementedError('do_work method on thread worker not implemented.')