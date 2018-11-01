from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt, QVariant


class JLAbstractTableModel(QAbstractTableModel):
    headers = []
    model = None

    def __init__(self, parent=None):
        super().__init__(parent)

        if not self.model:
            raise NotImplementedError("Model must be implemented")

        self.data = []

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]
        return QVariant()

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        [self.data.insert(position + row, self.model()) for row in range(rows)]
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        del self.data[position:position + rows]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.data)