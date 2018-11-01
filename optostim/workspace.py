import logging
from pathlib import Path

import jsonpickle
from PyQt5 import QtCore
from PyQt5.QtCore import QFileInfo, pyqtSignal

from optostim.common.paths import Paths

log = logging.getLogger(__name__)

EXTENSION = 'txt'


class Workspace(QtCore.QObject):

    workingDirectoryChanged = pyqtSignal(str)
    filenameChanged = pyqtSignal(str)
    dataLoaded = pyqtSignal(str)
    workspaceSaved = pyqtSignal(str)

    def __init__(self, filename="", working_directory="", parent=None):
        super().__init__(parent)
        self.working_path = Path(working_directory)
        self._working_directory = working_directory
        self._filename = filename

    def __setstate__(self, state):
        self.working_directory = state["_working_directory"]
        self.filename = state["_filename"]

    def full_path(self):
        return "{}{}.{}".format(self.working_directory, self.filename, EXTENSION)

    def load(self, destination, load_from):
        destination['workspace'] = self
        with open(load_from) as f:
            json_data = f.read()
        new_objects = jsonpickle.decode(json_data)

        for key, value in destination.items():
            try:
                vars_to_copy = new_objects[key]
            except KeyError as e:
                log.warning("Unrecognised key from saved data: {}".format(e))
            else:
                if hasattr(value, '__setstate__'):
                    value.__setstate__(vars_to_copy)
                else:
                    log.warning("Problem loading {} into {}.".format(value, vars_to_copy))

        self.dataLoaded.emit(load_from)

    def save(self, from_what):
        from_what['workspace'] = self
        jsonpickle.set_encoder_options(name='json', indent=4)

        save_as = self.save_filename()

        states = {}

        for k, v in from_what.items():
            if hasattr(v, '__getstate__'):
                state = v.__getstate__()
            else:
                state = v.__dict__.copy()
            states[k] = state

        pickled = jsonpickle.encode(states)

        with open(save_as, "w") as f:
            f.write(pickled)

        self.workspaceSaved.emit(save_as)

    def save_filename(self):
        file = "{}.{}".format(self.filename, EXTENSION)
        save_as = Paths.join(self.working_directory, file)
        count = 1
        while QFileInfo(save_as).exists():
            file = "{}_{}.{}".format(self.filename, count, EXTENSION)
            save_as = Paths.join(self.working_directory, file)
            count += 1
        return save_as

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, new_filename):
        self._filename = new_filename
        self.filenameChanged.emit(self._filename)

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, new_dir):
        self._working_directory = new_dir
        self.working_path = Path(new_dir)
        self.workingDirectoryChanged.emit(self._working_directory)
        log.info("Working directory is now: {}".format(self.working_directory))
