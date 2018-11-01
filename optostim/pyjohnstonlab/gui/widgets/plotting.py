from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class PyQtGraphWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = pg.GraphicsLayoutWidget()

        self.ax = pg.PlotWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        self.setLayout(layout)



