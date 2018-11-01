import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSizePolicy

from pyjohnstonlab.devices.camera_device import EXPOSURE, GAIN
from pyjohnstonlab.gui.widgets.camera.cameraexposurespinbox import CameraExposureSpinBox
from pyjohnstonlab.gui.widgets.camera.cameragainspinbox import CameraGainSpinBox
from pyjohnstonlab.gui.widgets.camera.camerapropertycombobox import CameraPropertyComboBox
from pyjohnstonlab.gui.widgets.camera.camerapropertydoublespinbox import CameraPropertyDoubleSpinBox

log = logging.getLogger(__name__)


class CameraControlsWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QGridLayout())

    def update_controls(self, camera_device):
        while self.layout().count() > 0:
            widget_item = self.layout().takeAt(0)
            if widget_item:
                widget_item.widget().deleteLater()

        max_width = 0

        widgets_to_add = []

        for i, p in enumerate(camera_device.properties):
            if not p.name.lower().find('exposure') == 0 and not p.name.lower().find('gain') == 0:
                label, display = self.update_control_by_name(camera_device, p.name)
                max_width = max(max_width, label.sizeHint().width() + display.sizeHint().width())
                widgets_to_add.append((label, display))

        # Different cameras may not have exposure as a property so we need to use specific custom spin box
        exposure_spin_box = CameraExposureSpinBox(device=camera_device)
        exposure_spin_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        label = QLabel(EXPOSURE)
        label.setAlignment(Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        widgets_to_add.append((label, exposure_spin_box))

        # Different cameras do not always have a property called just 'gain', e.g. might be 'gain(db)'.
        gain_spin_box = CameraGainSpinBox(device=camera_device)
        gain_spin_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        label = QLabel(GAIN)
        label.setAlignment(Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        widgets_to_add.append((label, gain_spin_box))

        alphabetical_widgets = sorted(widgets_to_add, key=lambda w: w[0].text())
        for i, widgets in enumerate(alphabetical_widgets):
            self.layout().addWidget(widgets[0], i, 0)
            self.layout().addWidget(widgets[1], i, 1)

        # todo - dynamic width for this based on contents

    def update_control_by_name(self, camera_device, property_name):

        cam_property = [p for p in camera_device.properties if p.name == property_name]

        if not cam_property:
            raise ValueError("Camera property name {} does not exist.".format(property_name))

        cam_property = cam_property[0]

        label = QLabel(cam_property.name)
        label.setAlignment(Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        if cam_property.read_only:
            try:
                display = QLabel("{}".format(cam_property.current))
            except AttributeError as e:
                log.debug("!!!!!!!!! Cam property: {}".format(cam_property.__dict__))
                raise AttributeError(e)
        elif cam_property.allowed_values:
            display = CameraPropertyComboBox(camera_device=camera_device, camera_property=cam_property)
        else:
            display = CameraPropertyDoubleSpinBox(camera_device=camera_device, camera_property=cam_property,
                                                  parent=self)

        display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
        return label, display
