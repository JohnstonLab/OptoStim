from PyQt5.QtWidgets import QApplication

from version import __version__


class Application(QApplication):

    def __init__(self, argv):
        super().__init__(argv)

        self.setOrganizationName("JohnstonLab")
        self.setApplicationVersion(__version__)