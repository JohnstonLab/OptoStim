import logging
from random import sample

from PyQt5.QtCore import QVariant, Qt, pyqtSignal

from pyjohnstonlab.mixins import JSONPickleMixin
from optostim.models.datamodels.stimulus_point import StimulusPoint
from pyjohnstonlab.gui.item_models import JLAbstractTableModel

log = logging.getLogger(__name__)

INDEX_COLUMN = 0
FRAME_COLUMN = 1
LOCATION_COLUMN = 2
INTENSITY_COLUMN = 3
SIZE_COLUMN = 4


class StimulusPointsListModel(JLAbstractTableModel):

    headers = ['Index', 'Frame', 'Location',  'Intensity', 'Size']
    model = StimulusPoint
    sizeChanged = pyqtSignal(float)

    def __init__(self, points=None, size=10, parent=None):
        super().__init__(parent)
    #    # self.points = points if points else []
        self._size = size

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __getstate__(self):
        data = []
        for point in self.data:
            data.append(point.__getstate__())
        return {'data': data, 'size': self.size}

    def __setitem__(self, key, value):
        self.setData(self.index(key), value)

    def __setstate__(self, state):
        self.size = state['size']
        points = state['data']

        self.removeRows(0, self.rowCount())

        for i, p in enumerate(points):
            if self.insertRow(self.rowCount()):
                row = self.rowCount() - 1
                self.setData(self.index(row, FRAME_COLUMN), p['frame'])
                self.setData(self.index(row, INDEX_COLUMN), p['index'])
                self.setData(self.index(row, INTENSITY_COLUMN), p['intensity'])
                self.setData(self.index(row, LOCATION_COLUMN), p['location'])
                self.setData(self.index(row, SIZE_COLUMN), p['size'])

            else:
                raise Exception("Could not insert stimulus point")

    def clear(self):
        self.data = []

    def data(self, model_index, role=None):
        if role == Qt.DisplayRole and len(self.data) > 0:
            stimulus_point = self.data[model_index.row()]
            column = model_index.column()
            if column == 0:
                return stimulus_point.index
            elif column == 1:
                return stimulus_point.frame
            elif column == 2:
                return "({:.2f}, {:.2f})".format(stimulus_point.location[0], stimulus_point.location[1])
            elif column == 3:
                return "{:.2f}".format(stimulus_point.intensity)
            elif column == 4:
                return stimulus_point.size
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return QVariant()

    def flags(self, model_index):
        if not model_index.isValid():
            return Qt.ItemIsEnabled

        flags = super().flags(model_index)

        if model_index.column() == INTENSITY_COLUMN:
            flags |= Qt.ItemIsEditable

        return flags

    def __iter__(self):
        return iter(self.data)

    def as_dict(self):
        return {'size': self.size, 'points': [point.to_dict() for point in self.points]}

    def sample(self, choose):
        return sorted(sample(self.data(), choose), key=lambda point: point.index)

    def setData(self, model_index, value, role=Qt.EditRole):
        if model_index.isValid() and (role == Qt.EditRole):
            stimulus_point = self.data[model_index.row()]
            column = model_index.column()
            log.debug("Row: {}, Column: {}, Value: {}".format(model_index.row(), column, value))
            if column == INDEX_COLUMN:
                stimulus_point.index = value
            elif column == FRAME_COLUMN:
                stimulus_point.frame = value
            elif column == LOCATION_COLUMN:
                stimulus_point.location = value
            elif column == INTENSITY_COLUMN:
                stimulus_point.intensity = value
            elif column == SIZE_COLUMN:
                stimulus_point.size = value
            else:
                assert "Should not get to here"
            self.dataChanged.emit(model_index, model_index)
            return True

        return False

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, new_size):
        self._size = new_size
        for i, _ in enumerate(self.data):
            self.setData(model_index=self.index(i, SIZE_COLUMN),  value=new_size)
        self.sizeChanged.emit(self._size)





