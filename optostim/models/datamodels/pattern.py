from PyQt5.QtGui import QIcon

from optostim.common.resources import Resources


class Pattern(object):
    icon_name = ""
    name = ""
    size = 16

    def __init__(self):
        self._icon = self.get_icon()

    @classmethod
    def get_icon(cls):
        return QIcon(Resources.get(cls.icon_name))

    @classmethod
    def icon(cls):
        return cls.get_icon()

    @classmethod
    def pixmap(cls, size=None):
        return cls.icon().pixmap(size if size else cls.size)