from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class Device(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection_timer = QTimer(parent=self)
        self._connection_timer.timeout.connect(self._query_connection)

    def _query_connection(self):
        raise NotImplementedError

