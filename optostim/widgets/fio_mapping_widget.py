import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QSizePolicy

from optostim.models.datamodels.protocol_element import PROPERTY_FIOS

log = logging.getLogger(__name__)


class FIOMappingWidget(QWidget):

    fioMappingChanged = pyqtSignal()

    def __init__(self, mapping, parent=None):
        super().__init__(parent)

        self.mapping = mapping

        label = QLabel("FIO{}".format(mapping.fio))
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.combo_box = QComboBox()
        self.combo_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        for prop in PROPERTY_FIOS:
            self.combo_box.addItem(prop.name.lower().capitalize(), prop)

        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.combo_box)

        self.setLayout(layout)

        self.connect()

    def connect(self):
        self.combo_box.currentIndexChanged.connect(self.on_combo_box_currentIndexChanged)
        self.mapping.protocolElementPropertyChanged.connect(self.on_protocolElementPropertyChanged)

    @pyqtSlot(int)
    def on_combo_box_currentIndexChanged(self, index):
       self.mapping.protocol_element_property = self.combo_box.itemData(index)

    def on_protocolElementPropertyChanged(self, old_value, new_value):
        index = self.combo_box.findData(new_value)
        self.combo_box.setCurrentIndex(index)

