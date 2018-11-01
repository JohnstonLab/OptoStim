from PyQt5.QtCore import QThread


class Thread(QThread):

    def __init__(self, parent, worker, on_finish=None, on_start=None):
        super().__init__(parent=parent)

        if on_start:
            self.started.connect(on_start)

        self.started.connect(worker.run)

        if on_finish:
            self.finished.connect(on_finish)

