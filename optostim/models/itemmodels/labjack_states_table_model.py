import logging

from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex, QDataStream

from pyjohnstonlab.mixins import JSONPickleMixin
from optostim.models.datamodels.labjack_state_model import LabJackStateModel

log = logging.getLogger(__name__)


class LabJackStatesTableModel(JSONPickleMixin, QAbstractTableModel):

    headers = ['FIO4', 'FIO5', 'FIO6', 'FIO7', 'DAC0', 'DAC1', 'Duration']
    mime_format = 'application/x-qabstractitemmodeldatalist'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.states = []

    def __setstate__(self, state):
        self.removeRows(0, self.rowCount())
        for i, s in enumerate(state['states']):
            model_index = self.index(i, 0)
            if not model_index.isValid() and not self.insertRow(self.rowCount()):
                raise Exception('Could not load in labjack state')
            self.setData(self.index(i, 0), s.FIO4State)
            self.setData(self.index(i, 1), s.FIO5State)
            self.setData(self.index(i, 2), s.FIO6State)
            self.setData(self.index(i, 3), s.FIO7State)
            self.setData(self.index(i, 4), s.DAC0)
            self.setData(self.index(i, 5), s.DAC1)
            self.setData(self.index(i, 6), s.duration)

            # for j, value in enumerate(s):
            #     if not self.setData(self.index(i, j), s[j]):
            #         raise Exception('Could not load in labjack state')

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.states)

    def canDropMimeData(self, QMimeData, Qt_DropAction, row, col, QModelIndex):
        if QMimeData.hasFormat(self.mime_format):
            incoming_states = self._decode_data(QMimeData)
            return len(incoming_states) == 1
        return False

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, model_index, role=None):
        if (role == Qt.DisplayRole or role == Qt.EditRole) and len(self.states) > 0:
            return self.states[model_index.row()][model_index.column()]
        return QVariant()

    def dropMimeData(self, data, drop_action, row, column, parent):
        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = self.rowCount()

        dragged_state = self._decode_data(data)[0]

        self.insertRow(begin_row)

        for column, data in enumerate(dragged_state):
            model_index = self.index(begin_row, column)
            self.setData(model_index=model_index, value=data, role=Qt.EditRole)

        return True

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | default_flags

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == Qt.DisplayRole:
            if Qt_Orientation == Qt.Horizontal:
                return self.headers[p_int]
            return p_int
        return QVariant()

    def add_state(self, fio4state=False, fio5state=False, fio6state=False, fio7state=False, dac0=0.0,
                 dac1=0.0, duration=0.0):
        if self.insertRow(self.rowCount()):
            self.states[-1] = LabJackStateModel(fio4state, fio5state, fio6state, fio7state, dac0, dac1, duration)
            self.dataChanged.emit(self.index(self.rowCount(), 0), self.index(self.rowCount(), self.columnCount()))
        else:
            raise Exception('Could not insert row')

    def insertRows(self, position, rows, model_index=QModelIndex()):
        self.beginInsertRows(model_index, position, position + rows - 1)
        for row in range(rows):
            self.states.insert(position + row, LabJackStateModel())
        self.endInsertRows()
        return True

    def moveRows(self, source_parent, source_row, count, destination_parent, destination_child):
        self.beginMoveRows(QModelIndex(), source_row, source_row + count - 1, QModelIndex(), destination_child)
        for row in range(count):
            self.states.insert(destination_child + row, self.states[source_row])
            remove_at_index = source_row if destination_child > source_row else source_row + 1
            self.states.pop(remove_at_index)
        self.endMoveRows()

        return True

    def removeRows(self, position, rows, index=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(index, position, position + rows - 1)
        del self.states[position:position + rows]
        self.endRemoveRows()
        return True

    def setData(self, model_index, value, role=Qt.EditRole):
        if model_index.isValid() and (role == Qt.EditRole):
            self.states[model_index.row()][model_index.column()] = value
            self.dataChanged.emit(model_index, model_index)
            return True
        return False

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

    def _decode_data(self, data):

        encoded_data = data.data(self.mime_format)
        stream = QDataStream(encoded_data)

        dragged_states = []
        dragged_state = []
        r_previous = None

        while not stream.atEnd():

            r = stream.readInt32()
            c = stream.readInt32()

            if r != (r_previous if r_previous else r):
                dragged_states.append(dragged_state)
                dragged_state.clear()
            r_previous = r

            num_items_in_map = stream.readUInt32()

            for i in range(num_items_in_map):
                key = stream.readInt32()
                value = QVariant()
                stream >> value
                dragged_state.append(value.value())

        dragged_states.append(dragged_state)

        return dragged_states




