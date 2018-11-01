import logging

from PyQt5.QtCore import QObject, pyqtSignal

from pyjohnstonlab.mixins import JSONPickleMixin

log = logging.getLogger(__name__)


class Transform(JSONPickleMixin, QObject):

    dxChanged = pyqtSignal(float)
    dyChanged = pyqtSignal(float)
    rotationChanged = pyqtSignal(float)
    scaleChanged = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.dx = 0.0
        self.dy = 0.0
        self.rotation = 0.0
        self.scale = 1.0

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        signal = getattr(self, "{}Changed".format(key), None)
        if signal:
            signal.emit(value)

    def __setstate__(self, state):
        for key, value in state.items():
            log.debug("Setting {} to {}".format(key, value))
            setattr(self, key, value)




