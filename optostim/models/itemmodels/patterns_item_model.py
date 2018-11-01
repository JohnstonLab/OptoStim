from PyQt5.QtCore import QAbstractItemModel, QVariant


class PatternsItemModel(QAbstractItemModel):

    def __init__(self, patterns, parent=None):
        super().__init__(parent)
        self.patterns = patterns

    def data(self, model_index, role=None):
        return 'always'


    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.patterns)