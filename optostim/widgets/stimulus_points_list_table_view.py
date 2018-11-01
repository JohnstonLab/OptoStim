from PyQt5.QtWidgets import QTableView, QHeaderView


class StimulusPointsListTableView(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resizeColumnsToContents()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        print('key press on custom table view')