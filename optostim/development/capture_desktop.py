import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


class ShootScreenWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.image_label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.shoot_screen)
        self.timer.setInterval(1000)
        self.timer.start()

    def shoot_screen(self):
        screens = QGuiApplication.screens()
        self.image_label.setPixmap(screens[0].grabWindow(0))

app = QApplication(sys.argv)

w = ShootScreenWidget()
w.resize(250, 150)
w.move(300, 300)
w.setWindowTitle('Capture Desktop')
w.shoot_screen()
w.show()

sys.exit(app.exec_())