from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class MatplotlibWidget(QWidget):

    def __init__(self, navigation_toolbar=False, parent=None):
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        # compare to True instead of using "if navigation_toolbar:" as widget promotion sends in the parent as 2nd arg.
        if navigation_toolbar == True:
            self.toolbar = NavigationToolbar(self.canvas, self)
            layout.addWidget(self.toolbar)

        self.setLayout(layout)

    def add_navigation_toolbar(self):
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().insertWidget(-1, self.toolbar)

    def plot(self):
        pass