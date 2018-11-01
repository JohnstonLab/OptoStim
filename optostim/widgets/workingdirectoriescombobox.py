import logging

from PyQt5.QtCore import QCoreApplication, QSettings, pyqtSlot
from PyQt5.QtWidgets import QComboBox

WORKING_DIR_HISTORY = 'workingDirectoryHistory'

log = logging.getLogger(__name__)


class WorkingDirectoriesComboBox(QComboBox):

    def __init__(self, parent):
        super().__init__(parent)
        self.settings = QSettings(QCoreApplication.organizationName(), QCoreApplication.applicationName())
        self._workspace = None
        self.currentTextChanged.connect(self.on_currentTextChanged)

    @pyqtSlot(str)
    def on_currentTextChanged(self, text):
        index = self.findText(text)

        if index > 0:

            self.currentTextChanged.disconnect(self.on_currentTextChanged)
            self.workspace.workingDirectoryChanged.disconnect(self.on_workspace_workingDirectoryChanged)

            self.removeItem(index)
            self.insertItem(0, text)
            self.setCurrentIndex(0)
            self.workspace.working_directory = text
            items = set(self.itemText(i) for i in range(self.count()) if self.itemText(i))
            self.settings.setValue(WORKING_DIR_HISTORY, items)

            self.currentTextChanged.connect(self.on_currentTextChanged)
            self.workspace.workingDirectoryChanged.connect(self.on_workspace_workingDirectoryChanged)

    @pyqtSlot(str)
    def on_workspace_workingDirectoryChanged(self, new_dir):
        index = self.findText(new_dir)

        self.currentTextChanged.disconnect(self.on_currentTextChanged)

        if index > 0:
            self.removeItem(index)
            self.insertItem(0, new_dir)
            self.setCurrentIndex(0)
        elif index == -1:
            self.insertItem(0, new_dir)
            self.setCurrentIndex(0)

        items = set(self.itemText(i) for i in range(self.count()) if self.itemText(i))

        self.settings.setValue(WORKING_DIR_HISTORY, items)

        self.currentTextChanged.connect(self.on_currentTextChanged)

    @property
    def workspace(self):
        return self._workspace

    @workspace.setter
    def workspace(self, ws):
        if ws != self.workspace:
            self._workspace = ws
            working_directory_history = self.settings.value(WORKING_DIR_HISTORY, [])

            if working_directory_history:
                for dir in set(working_directory_history):
                    self.addItem(dir)
            self.setCurrentIndex(0)
            self._workspace.workingDirectoryChanged.connect(self.on_workspace_workingDirectoryChanged)
