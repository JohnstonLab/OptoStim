from itertools import cycle

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout


class StatusWidget(QWidget):

    def __init__(self, status_label, initial_value='', colours=None):
        super().__init__()

        self.status_label = QLabel()
        self.status_label.setText(status_label)

        self.value = QLabel()

        layout = QHBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.value)

        self.setLayout(layout)

        self.colour_cycle = cycle(colours) if colours else None
        self.update_status(initial_value)

    def update_status(self, new_value):
        self.value.setText(new_value)

        if self.colour_cycle:
            self.setStyleSheet('background-color: %s' % next(self.colour_cycle))