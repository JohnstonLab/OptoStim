import logging
import os
from enum import Enum

from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex, pyqtSignal, QDataStream, QSize
# todo - better name!
from PyQt5.QtGui import QPixmap, QImage

from optostim.models.datamodels.patterns.normal_pattern import NormalPattern
from optostim.models.datamodels.protocol_element import ProtocolElement, ProtocolElementProperty

log = logging.getLogger(__name__)


class ProtocolSequence(QAbstractTableModel):
    # todo - below is verbose, refactor at some point to be nice and neat, not DRY
    headers = [
        'Stimulus Points',
        'Laser',
        'Pmt',
        'Sync',
        'Wait',
        'Duration'
    ]
    mime_format = 'application/x-qabstractitemmodeldatalist'

    patternChanged = pyqtSignal(object)
    randomSeedChanged = pyqtSignal(int)
    run = pyqtSignal()

    class Roles(Enum):
        STIMULUS_POINTS = Qt.UserRole

    def __init__(self, sequence=None, parent=None):
        super().__init__(parent)
        self.protocol = sequence if sequence else []
        self._pattern = None
        self._random_seed = None

    def __getstate__(self):
        state = [e.__getstate__() for e in self.protocol]
        return {'pattern': self.pattern, 'protocol': state, 'random_seed': self.random_seed}

    def __iter__(self):
        return iter(self.protocol)

    def __len__(self):
        return len(self.protocol)

    def __setstate__(self, state):
        self.loaded_in_protocol = state
        self.random_seed = state['random_seed']

    def _decode_data(self, data):
        encoded_data = data.data(self.mime_format)
        stream = QDataStream(encoded_data)

        dragged_data = []

        while not stream.atEnd():
            row = stream.readInt32()
            column = stream.readInt32()

            num_items_in_map = stream.readUInt32()
            item = {'row': row, 'column': column, 'map items': {}}
            for i in range(num_items_in_map):
                key = stream.readInt32()
                value = QVariant()
                stream >> value
                item['map items'][Qt.ItemDataRole(key)] = value.value()

            dragged_data.append(item)

        return dragged_data

    def add_element(self, stimulus_points, laser, pmt, sync, wait, duration):
        if self.insertRow(self.rowCount()):
            model_index = self.index(self.rowCount() - 1, 0)
            self.setData(model_index, stimulus_points, role=Qt.EditRole)

            model_index = self.index(self.rowCount() - 1, 1)
            self.setData(model_index, laser, role=Qt.EditRole)

            model_index = self.index(self.rowCount() - 1, 2)
            self.setData(model_index, pmt, role=Qt.EditRole)

            model_index = self.index(self.rowCount() - 1, 3)
            self.setData(model_index, sync, role=Qt.EditRole)

            model_index = self.index(self.rowCount() - 1, 4)
            self.setData(model_index, wait, role=Qt.EditRole)

            model_index = self.index(self.rowCount() - 1, 5)
            self.setData(model_index, duration, role=Qt.EditRole)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, model_index, role=Qt.DisplayRole):

        column = model_index.column()
        element = self.protocol[model_index.row()]
        #  todo - ugly ugly! refactor, make neat
        if role == Qt.DisplayRole and len(self.protocol) > 0:
            if column == ProtocolElementProperty.STIMULUSPOINTS:
                return ', '.join(str(point.index()) for point in element.stimulus_points)
            elif column == ProtocolElementProperty.LASER:
                return 'On' if element.laser else ''
            elif column == ProtocolElementProperty.PMT:
                return 'On' if element.pmt else ''
            elif column == ProtocolElementProperty.SYNC:
                return 'On' if element.sync else ''
            elif column == ProtocolElementProperty.DURATION and not element.wait:
                return element.duration
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.DecorationRole:
            if column == ProtocolElementProperty.WAIT and element.wait:
                working_dir = os.getcwd()
                img_location = 'resources\clock.png'
                path = os.path.join(working_dir, img_location)
                pixmap = QPixmap.fromImage(QImage(path))
                size = 16
                return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif role == self.Roles.STIMULUS_POINTS.value:
            return element.stimulus_points
        elif role == Qt.SizeHintRole and column == 0:
            #  todo - no to hard coded for size passed to sizehint delegate
            if element.stimulus_points:
                height = 33 if element.stimulus_points else 0
                return QSize(len(element.stimulus_points) * 18, height)

        return QVariant()

    def dropMimeData(self, mime_data, drop_action, row, column, parent):
        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = self.rowCount()

        dragged_data = self._decode_data(mime_data)

        dragged_row_indices = set([data['row'] for data in dragged_data])

        rows_to_move = [self.protocol[i] for i in list(dragged_row_indices)]

        self.insertRows(begin_row, len(dragged_row_indices))

        for i, element in enumerate(rows_to_move):
            model_index = self.index(begin_row + i, 0)
            self.setData(model_index, element.stimulus_points, role=Qt.EditRole)

            model_index = self.index(begin_row + i, 1)
            self.setData(model_index, element.laser, role=Qt.EditRole)

            model_index = self.index(begin_row + i, 2)
            self.setData(model_index, element.pmt, role=Qt.EditRole)

            model_index = self.index(begin_row + i, 3)
            self.setData(model_index, element.sync, role=Qt.EditRole)

            model_index = self.index(begin_row + i, 4)
            self.setData(model_index, element.wait, role=Qt.EditRole)

            model_index = self.index(begin_row + i, 5)
            self.setData(model_index, element.duration, role=Qt.EditRole)

        return True

    def flags(self, index):

        default_flags = super().flags(index)

        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | default_flags

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == Qt.DisplayRole:
            if Qt_Orientation == Qt.Horizontal:
                return self.headers[p_int]
            return p_int
        return QVariant()

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        [self.protocol.insert(position + row, ProtocolElement()) for row in range(0, rows)]
        self.endInsertRows()
        return True

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, new_pattern):
        if not new_pattern == self.pattern:
            self._pattern = new_pattern
            self.patternChanged.emit(new_pattern)
        for i in range(self.rowCount()):
            index = self.index(i, 0)
            points = self.data(index, role=self.Roles.STIMULUS_POINTS.value)
            for point in points:
                if not point.pattern is NormalPattern:
                    point.pattern = new_pattern
            self.setData(index=index, value=points)

    @property
    def random_seed(self):
        return self._random_seed

    @random_seed.setter
    def random_seed(self, new_seed):
        if self.random_seed != new_seed:
            self._random_seed = new_seed
            self.randomSeedChanged.emit(self.random_seed)

    def removeRows(self, position, rows, index=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        del self.protocol[position:position+rows]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.protocol)

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and (role == Qt.EditRole):
            element = self.protocol[index.row()]
            column = index.column()
            if column == 0:
                element.stimulus_points = value
            elif column == 1:
                element.laser = value
            elif column == 2:
                element.pmt = value
            elif column == 3:
                element.sync = value
            elif column == 4:
                element.wait = value
            elif column == 5:
                element.duration = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction



