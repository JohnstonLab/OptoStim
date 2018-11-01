import logging

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHeaderView, QAbstractItemView

from optostim.common import views
from optostim.models.protocol_sequence_delegate import ProtocolSequenceDelegate

log = logging.getLogger(__name__)


class ProgramElement(QWidget):

    def __init__(self, loop_number, parent=None):
        super().__init__(parent)

        uic.loadUi(views.get('program_element.ui'), self)

        self.loop_number = loop_number
        self.loopNumberLabel.setText(str(loop_number))
        self._update_table_height()

    def _required_table_height(self):
        total_height = self.tableView.horizontalHeader().height()
        total_height *= 2

        model = self.tableView.model()

        if model:
            for row in range(0, model.rowCount()):
                total_height += self.tableView.rowHeight(row)

        return total_height

    def setup_tableview(self, model, draggable=True):
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableView.horizontalHeader().setStretchLastSection(True)

        self.tableView.setItemDelegate(ProtocolSequenceDelegate())
        self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableView.verticalScrollBar().setDisabled(True)
        self.tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.update_model(new_model=model)

        if draggable:
            self.tableView.setAcceptDrops(True)
            self.tableView.setDragEnabled(True)
            self.tableView.setDefaultDropAction(Qt.MoveAction)
            self.tableView.setDragDropMode(QAbstractItemView.InternalMove)
            self.tableView.setDragDropOverwriteMode(False)
            self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)

    def update_model(self, new_model):
        self.tableView.setModel(new_model)
        self.tableView.model().dataChanged.connect(lambda: self._update_table_height())
        self.tableView.model().layoutChanged.connect(lambda: self._update_table_height())
        self.tableView.model().rowsRemoved.connect(lambda: self._update_table_height())
        self.tableView.resizeRowsToContents()

        self._update_table_height()
        #self.tableView.update()

    def _update_table_height(self):
        height = self._required_table_height()
        self.tableView.setMaximumHeight(height)
        self.tableView.setMinimumHeight(height)
