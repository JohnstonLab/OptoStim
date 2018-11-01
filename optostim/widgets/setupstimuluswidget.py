import json
import logging
import os

from PyQt5.QtCore import pyqtSlot, Qt, QDir
from PyQt5.QtGui import QBrush, QResizeEvent, QImage, QGuiApplication, QTransform
from PyQt5.QtWidgets import QWidget, QFileDialog, QHeaderView, QGraphicsScene

from optostim.development.widget_abstraction import loadUI
from optostim.graphics.stimulusgraphicsscene import StimulusGraphicsScene
from optostim.widgets.camera_homograph_setup_widget import CameraHomographySetupWidget
from optostim.widgets.camera_window import CameraWindow
from optostim.widgets.homography_stimulus_window_widget import HomographyStimulusWindowWidget
from optostim.widgets.intensity_mask_setup_widget import IntensityMaskSetupWidget
from pyjohnstonlab.devices.camera_device import CameraDevice
from pyjohnstonlab.devices.exceptions import DeviceException
from .scanimage_widget import ScanImageWidget

log = logging.getLogger(__name__)


DEVICE_ADAPTERS = 'deviceAdapters'


class SetupStimulusWidget(QWidget):

    def __init__(self,
                 parent, camera, intensity_mask, homography_transform_stimulus_window, labjack, settings,
                 stimulus_points, stimulus_widget, workspace, image_stack, camera_transform):
        super().__init__(parent=parent)
        self.camera = camera
        self.camera_needs_initialising = True
        self.camera_widget = CameraWindow(camera_device=camera, workspace=workspace)
        self.experiment_scene = StimulusGraphicsScene()
        self.homography_transform = homography_transform_stimulus_window
        self.homography_stimulus_widget = HomographyStimulusWindowWidget(camera=camera,
                                                                         homography_transform=homography_transform_stimulus_window,
                                                                         stimulus_widget=stimulus_widget)
        self.homography_setup_scene = StimulusGraphicsScene()
        self.image_stack = image_stack
        self.intensity_mask = intensity_mask
        self.matplotlib_widget = ScanImageWidget(model=stimulus_points,
                                                 image_stack=image_stack, scene=self.experiment_scene)
        self.plot_data = ''
        self.qt_image = QImage()
        self.settings = settings

        self.stimulus_points = stimulus_points
        self.stimulus_widget = stimulus_widget
        self.stimulus_widget.setScene(self.experiment_scene)
        self.transform = camera_transform
        self.workspace = workspace

        current_directory = os.path.dirname(__file__)
        relative_location = '../views/SetupStimulusView.ui'

        path = os.path.join(current_directory, relative_location)

        loadUI(path, self)
        self.imageStackFilename_control.value = ""

        self.intensity_mask_setup_widget = IntensityMaskSetupWidget(camera=self.camera,
                                                                    intensity_mask=intensity_mask,
                                                                    stimulus_widget=self.stimulus_widget)
        self.camera_homograph_widget = CameraHomographySetupWidget(camera=self.camera, camera_initialisation=self.initialise_camera)

        self.stimulusSquareSize.setText('%.2f μm' % self.stimulus_points.size)

        self.stimulusPointsTableView.setModel(self.stimulus_points)
        self.stimulusPointsTableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stimulusPointsTableView.resizeColumnsToContents()

        for item in self.camera.get_device_adapter_names():
            self.deviceAdaptersComboBox.addItem(item)

        self.fio4StateLabelComboBox.set(labjack, labjack.fio4)
        self.fio5StateLabelComboBox.set(labjack, labjack.fio5)
        self.fio6StateLabelComboBox.set(labjack, labjack.fio6)
        self.fio7StateLabelComboBox.set(labjack, labjack.fio7)

        self.fio4StateRadioButton.set(labjack, 4)
        self.fio5StateRadioButton.set(labjack, 5)
        self.fio6StateRadioButton.set(labjack, 6)
        self.fio7StateRadioButton.set(labjack, 7)

        self.workingDirectoriesComboBox.workspace = workspace
        self.connect()
        self.read_settings()
        log.info("Setup stimulus tab init complete.")

    def connect(self):
        self.homography_stimulus_widget.closed.connect(self.on_homographyStimulusWidget_closed)

        self.image_stack.dataChanged.connect(self.on_image_stack_dataChanged)
        # self.image_stack.fovChanged.connect(lambda value: self.FOV.setText("%.2f" % value))
        # self.image_stack.zoomChanged.connect(lambda value: self.zoom.setText("FOV @ Zoom %.2f:" % value))

        self.intensity_mask.isSetChanged.connect(lambda state: self.applyIntensityMaskCheckBox.setEnabled(state))

        self.stimulus_points.sizeChanged.connect(lambda value: self.stimulusSquareSize.setText('%.2f μm' % value))

        # self.transform.dxChanged.connect(lambda value: self.xTranslateDoubleSpinBox_control.set_value(value))
        # self.transform.dxChanged.connect(lambda value: self.stimulus_widget.set_translation(self.transform.dx, -self.transform.dy))
        #
        # self.transform.dyChanged.connect(lambda value: self.yTranslateDoubleSpinBox_control.set_value(value))
        # self.transform.dyChanged.connect(lambda value: self.stimulus_widget.set_translation(self.transform.dx, -self.transform.dy))
        # self.transform.rotationChanged.connect(lambda value: self.rotationDoubleSpinBox_control.set_value(value))
        # self.transform.rotationChanged.connect(lambda value: self.stimulus_widget.set_rotation(value))
        # self.transform.scaleChanged.connect(lambda value: self.scaleDoubleSpinBox_control.set_value(value))
        # self.transform.scaleChanged.connect(lambda value: self.stimulus_widget.set_scale(value))

        self.workspace.workingDirectoryChanged.connect(self.on_workspace_workingDirectoryChanged)

        # self.xTranslateDoubleSpinBox_control.qt_control.valueChanged.connect(
        #     lambda value: setattr(self.transform, 'dx', value))
        # self.yTranslateDoubleSpinBox_control.qt_control.valueChanged.connect(
        #     lambda value: setattr(self.transform, 'dy', value))
        # self.rotationDoubleSpinBox_control.qt_control.valueChanged.connect(
        #     lambda value: setattr(self.transform, 'rotation', value))
        # self.scaleDoubleSpinBox_control.qt_control.valueChanged.connect(
        #     lambda value: setattr(self.transform, 'scale', value))

    def closeEvent(self, event):
        log.info("Closing setup stimulus widget")
        self.settings.setValue('deviceAdapters', self.deviceAdaptersComboBox.currentText())
        self.stimulus_widget.close()
        event.accept()

    @staticmethod
    def get_available_cameras():
        device_classes = CameraDevice.__subclasses__()
        return [klass() for klass in device_classes]

    def hideEvent(self, hide_event):
        super().hideEvent(hide_event)
        # if not hide_event.spontaneous():
        #     self.stimulus_widget.hide_crosshair()

    def initialise_camera(self):
        if self.camera_needs_initialising:
            self.camera.initialise(adapter=self.deviceAdaptersComboBox.currentText(),
                                   device=self.availableCamerasComboBox.currentText())
            self.camera_needs_initialising = False

    def on_applyHomographyCheckBox_stateChanged(self, state):
        self.camera.use_homography_matrix = state

    @pyqtSlot(int)
    def on_applyIntensityMaskCheckBox_stateChanged(self, state):
        log.debug("on_applyIntensityMaskCheckBox_stateChanged")
        #self.intensity_mask.apply = state
        self.stimulus_widget.apply_intensity_mask = state

    @pyqtSlot(bytes)
    def on_arduino_newDataReceived(self, data):
        try:
            self.plot_data += data.decode()
        except UnicodeDecodeError as e:
            log.warning(e)
        else:
            def as_data_point(dct):
                if "x" in dct and "y" in dct:
                    return dct
                return None

            splitted = self.plot_data.split('\n')

            for result in splitted:
                try:
                    xy = json.loads(result, object_hook=as_data_point)
                except json.JSONDecodeError:
                    pass
                else:
                    if xy:
                        try:
                            self.respiration_widget.append(xy["x"], xy["y"])
                        except TypeError:
                            pass
                        else:
                            result_start = self.plot_data.find(result)
                            remove_up_to = result_start + len(result) + 1
                            self.plot_data = self.plot_data[remove_up_to:]

    @pyqtSlot(int)
    def on_availableCamerasComboBox_currentIndexChanged(self, index):
        self.camera_needs_initialising = True

    def on_cameraDevice_disconnected(self):
        index = self.availableCameras.findText(self.sender().module)
        self.availableCameras.setItemData(index, QBrush(Qt.red), Qt.TextColorRole)

    def on_cameraDevice_initialised(self):
        index = self.avilableCameras.findText(self.sender().module)
        self.availableCameras.setItemData(index, QBrush(Qt.black), Qt.TextColorRole)

    @pyqtSlot()
    def on_cameraWindow_pressed(self):
        self.initialise_camera()
        self.camera_widget.show()

    @pyqtSlot(str)
    def on_deviceAdaptersComboBox_currentIndexChanged(self, text):
        self.availableCamerasComboBox.clear()
        try:
            cameras = self.camera.get_available_device(library=text)
        except DeviceException as error:
            log.warning(error)
        else:
            for cam in cameras:
                self.availableCamerasComboBox.addItem(cam)

    @pyqtSlot()
    def on_homographButton_pressed(self):
        self.camera_homograph_widget.show()

    def on_openScanImage_pressed(self):
        if not self.matplotlib_widget.has_image:
            if self.matplotlib_widget.open_image_stack():
                self.matplotlib_widget.show()
        else:
            self.matplotlib_widget.show()

    @pyqtSlot(int)
    def on_crosshairThickness_valueChanged(self, value):
        self.stimulus_widget.crosshair_thickness = value

    @pyqtSlot()
    def on_homographyStimulusWidget_closed(self):
        log.debug("on_homographyStimulusWidget_closed")
        self.stimulus_widget.setScene(self.experiment_scene)
        self.stimulus_widget.open()

    @pyqtSlot()
    def on_image_stack_dataChanged(self):
        self.imageStackFilename_control.value = self.image_stack.file

    @pyqtSlot(int)
    def on_invertCheckBox_stateChanged(self, state):
        self.stimulus_widget.invert = state

    @pyqtSlot()
    def on_obtainMaskButton_pressed(self):
        self.initialise_camera()
        if not self.stimulus_widget.isVisible():
            self.stimulus_widget.open()
        self.intensity_mask_setup_widget.show()

    def on_openStimulusWindow_pressed(self):
        self.stimulus_widget.close() if self.stimulus_widget.isVisible() else self.stimulus_widget.open()

    @pyqtSlot()
    def on_respirationButton_pressed(self):
        self.respiration_widget.show()

    def on_stimulusWindowBackgroundColour_valueChanged(self, value):
        self.stimulus_widget.set_background_colour(float(value))

    @pyqtSlot()
    def on_scaleBarButton_pressed(self):
        self.stimulus_widget.show_scale_bar = not self.stimulus_widget.show_scale_bar

    @pyqtSlot(int)
    def on_scaleBarThicknessSpinBox_valueChanged(self, value):
        self.stimulus_widget.scale_bar_thickness = value

    @pyqtSlot(int)
    def on_scaleBarWidthSpinBox_valueChanged(self, value):
        self.stimulus_widget.scale_bar_width = value

    @pyqtSlot(QResizeEvent)
    def on_stimulus_widget_resized(self, resize_event):
        half_width = 0.5 * resize_event.size().width()
        half_height = 0.5 * resize_event.size().height()
        self.xTranslateDoubleSpinBox.setRange(-half_width, half_width)
        self.yTranslateDoubleSpinBox.setRange(-half_height, half_height)

    @pyqtSlot()
    def on_stimulusWindow_framesSwapped(self):
        screens = QGuiApplication.screens()
        pixmap = screens[1].grabWindow(0)
        self.stimulusWindowPreview.image = QImage(pixmap)

    @pyqtSlot(int)
    def on_stimulusWindowPreviewCheckBox_stateChanged(self, state):
        pass
        # if state:
        #     self.stimulus_widget.frameSwapped.connect(self.on_stimulusWindow_framesSwapped)
        #     self.on_stimulusWindow_framesSwapped()
        # else:
        #     self.stimulus_widget.frameSwapped.disconnect(self.on_stimulusWindow_framesSwapped)

    @pyqtSlot()
    def on_stimulusWindowHomographyButton_pressed(self):
        self.initialise_camera()
        self.stimulus_widget.setScene(self.homography_setup_scene)
        self.stimulus_widget.open()
        self.homography_stimulus_widget.show()

    @pyqtSlot(int)
    def on_stimulusWindowHomographyCheckBox_stateChanged(self, state):
        if state:
            # rect = self.stimulus_widget.scene().sceneRect()
            # transform = QTransform()
            # transform.translate(rect.center().x() + self.stimulus_widget.dx, rect.center().y() + self.stimulus_widget.dy)
            # transform = transform * self.homography_transform.transform
            # transform.translate(-rect.center().x() - self.stimulus_widget.dx, -rect.center().y() - self.stimulus_widget.dy)
            self.stimulus_widget.apply_transform(self.homography_transform.transform)
        else:
            self.stimulus_widget.setTransform(QTransform())

    def on_toggleCrosshair_pressed(self):
        self.stimulus_widget.crosshair = not self.stimulus_widget.crosshair

    @pyqtSlot()
    def on_workingDirectoryButton_pressed(self):
        path = QFileDialog.getExistingDirectory(self, "Select working directory", "", QFileDialog.ShowDirsOnly)
        if path:
            self.workspace.working_directory = QDir.toNativeSeparators(path)

    @pyqtSlot(str)
    def on_workspace_workingDirectoryChanged(self, new_dir):
        # self.workingDirectoriesComboBox.on_workspace_workingDirectoryChanged(new_dir)
        self.camera.working_path = new_dir

    def read_settings(self):
        previous_adapter = self.settings.value(DEVICE_ADAPTERS)
        if previous_adapter:
            self.deviceAdaptersComboBox.setCurrentIndex(self.deviceAdaptersComboBox.findText(previous_adapter))











