import logging
import os
import random
from math import sin, pi

from PyQt5.QtCore import pyqtSlot, QSettings, QCoreApplication, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QPushButton, QToolBar, QLabel, QLineEdit, \
    QFileDialog, QApplication

from optostim.graphics.stimulusgraphicsscene import StimulusGraphicsScene
from optostim.models.datamodels.homographytransform import HomographyTransform
from optostim.models.datamodels.image_stack import ImageStack
from optostim.models.datamodels.intensity_mask import IntensityMask
from optostim.models.datamodels.transform import Transform
from optostim.models.itemmodels.labjack_states_table_model import LabJackStatesTableModel
from optostim.models.itemmodels.protocol_sequence import ProtocolSequence
from optostim.models.itemmodels.stimulus_points_list_model import StimulusPointsListModel
from optostim.widgets.protocol_design.protocol_design_widget import ProtocolDesignWidget
from optostim.widgets.setupstimuluswidget import SetupStimulusWidget
from optostim.widgets.status_widget import StatusWidget
from optostim.widgets.stimulus_widget import StimulusWindowGraphicsView
from optostim.workspace import Workspace
from pyjohnstonlab.devices.arduino import ArduinoDevice
from pyjohnstonlab.devices.camera_device import CameraDevice
from pyjohnstonlab.devices.labjack_device import LabJackDevice
from pyjohnstonlab.gui import message_boxes
from pyjohnstonlab.gui.widgets.labjackwidget import LabJackWidget
from pyjohnstonlab.gui.widgets.respiration_rate_widget import RespirationRateWidget

log = logging.getLogger(__name__)


class Dependencies(QObject):

    def __init__(self, parent):
        super().__init__(parent)
        self.arduino = ArduinoDevice()
        self.camera = CameraDevice(parent=self)
        self.camera_transform = Transform()
        self.intensity_mask = IntensityMask()
        self.homography_stimulus_window = HomographyTransform(parent=self)
        self.image_stack = ImageStack()
        self.labjack = LabJackDevice(fio4_label='Laser',
                                     fio5_label='PMT',
                                     fio6_label='Sync',
                                     fio7_label='Wait',
                                     parent=self)
        self.labjack_states = LabJackStatesTableModel()
        self.stimulus_graphics_scene = StimulusGraphicsScene()
        self.stimulus_points = StimulusPointsListModel()
        self.protocol_sequence = ProtocolSequence()

    def clean_up(self):
        self.camera.unload()
        self.labjack.close()


class OptoStimMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.debug_time = 0
        self.dependencies = Dependencies(parent=self)
        self.workspace = Workspace(filename="workspace", working_directory=os.path.dirname(__file__))

        QApplication.setApplicationName("OptoStim")
        QApplication.setOrganizationName("JohnstonLab")

        self.setWindowTitle('OptoStim')
        self.settings = QSettings(QCoreApplication.organizationName(),QCoreApplication.applicationName())

        # self.stimulus_window = StimulusWidget(homography_transform=self.dependencies.homography_stimulus_window)
        self.stimulus_window = StimulusWindowGraphicsView(intensity_mask=self.dependencies.intensity_mask,
                                                          homography_transform=self.dependencies.homography_stimulus_window)

       # uic.loadUi('views/MainWindow.ui', self)

        #return
        self.setup_stimulus_widget = SetupStimulusWidget(camera=self.dependencies.camera,
                                                         camera_transform=self.dependencies.camera_transform,
                                                         homography_transform_stimulus_window=self.dependencies.homography_stimulus_window,
                                                         image_stack=self.dependencies.image_stack,
                                                         intensity_mask=self.dependencies.intensity_mask,
                                                         labjack=self.dependencies.labjack,
                                                         parent=self,
                                                         settings=self.settings,
                                                         stimulus_points=self.dependencies.stimulus_points,
                                                         stimulus_widget=self.stimulus_window,
                                                         workspace=self.workspace)

        self.labjack_widget = LabJackWidget(labjack=self.dependencies.labjack,
                                            labjack_states=self.dependencies.labjack_states,
                                            parent=self)
        self.respiration_widget = RespirationRateWidget(take_ft_at_seconds=20.0)
        self.protocol_design_widget = ProtocolDesignWidget(image_stack=self.dependencies.image_stack,
                                                           intensity_mask=self.dependencies.intensity_mask,
                                                           labjack=self.dependencies.labjack,
                                                           stimulus_points=self.dependencies.stimulus_points,
                                                           selected_stimulus_points=self.dependencies.protocol_sequence,
                                                           stimulus_widget=self.stimulus_window,
                                                           workspace=self.workspace,
                                                           parent=self)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.setup_stimulus_widget, "Setup Stimulus")
        self.tab_widget.addTab(self.labjack_widget, "LabJack Setup")
        self.tab_widget.addTab(self.protocol_design_widget, "Protocol Design")

        self.setCentralWidget(self.tab_widget)
        self.setWindowIcon(QIcon('OptoStimLogo.jpeg'))

        self.arduino_status_label = QLabel("Arduino Off")
        self.statusBar().addPermanentWidget(self.arduino_status_label)

        self.respiration_monitor = QPushButton("Start Monitoring")
        self.statusBar().addPermanentWidget(self.respiration_monitor)

        self.respiration_plot_button = QPushButton("Respiration Plot")
        self.statusBar().addPermanentWidget(self.respiration_plot_button)

        self.labjack_status = StatusWidget(status_label='LabJack Status:', initial_value='Disconnected')

        self.statusBar().addPermanentWidget(self.labjack_status)

        self.stimulus_window_status = StatusWidget(status_label='Stimulus Window:', initial_value='Off',
                                                   colours=['red', 'green'])

        self.statusBar().addPermanentWidget(self.stimulus_window_status)

        self.setup_menuBar()

        self.is_stimulating = False

        save_toolbar = QToolBar()
        save_toolbar.setMovable(False)
        save_toolbar.setFloatable(False)

        self.addToolBar(save_toolbar)

        label = QLabel("Filename")
        save_toolbar.addWidget(label)

        self.save_filename = QLineEdit("workspace")
        save_toolbar.addWidget(self.save_filename)

        self.save_workspace_button = QPushButton("Save workspace")
        save_toolbar.addWidget(self.save_workspace_button)

        self.load_workspace_button = QPushButton("Load")
        save_toolbar.addWidget(self.load_workspace_button)

        self.save_instances = [self.setup_stimulus_widget]

        self.connect()

    def connect(self):

        self.dependencies.labjack.connected.connect(lambda: self.labjack_status.update_status('Connected'))
        self.dependencies.labjack.disconnected.connect(lambda: self.labjack_status.update_status('Disconnected'))

#        self.protocol_design_widget.programStarted.connect(self.on_programStarted)

        self.respiration_plot_button.pressed.connect(self.on_respiration_plot_button_pressed)
        self.respiration_monitor.pressed.connect(self.on_respiration_monitor_button_pressed)

        self.stimulus_window.visibilityChanged.connect(self.on_stimulus_window_visibilityChanged)

        self.save_filename.textEdited.connect(self.on_save_filename_textEdited)
        self.save_workspace_button.pressed.connect(self.on_save_workspace_button_pressed)
        self.load_workspace_button.pressed.connect(self.on_load_workspace_button_pressed)

        self.workspace.dataLoaded.connect(lambda loaded_from:
                                          message_boxes.information(self, title="Data Loaded",
                                                                    text='Data loaded in from {}'.format(loaded_from)))
        self.workspace.filenameChanged.connect(lambda text: self.save_filename.setText(text))
        self.workspace.workspaceSaved.connect(
            lambda saved_as: message_boxes.information(self, title="Workspace Saved",
                                                       text="Saved to {} as {}"
                                                       .format(self.workspace.working_directory, saved_as)))

    def clean_up(self):
        log.info("Cleaning up")
        self.setup_stimulus_widget.close()
        self.dependencies.clean_up()
        log.info("Clean up complete")

    def closeEvent(self, event):
        super().closeEvent(event)
        QApplication.closeAllWindows()
        # self.clean_up()
        QApplication.quit()
        event.accept()

    def on_fioMappingChanged(self, old_value, new_value):
        for mapping in self.labjack_mappings:
            if not mapping == self.sender():
                if mapping.protocol_element_property == new_value:
                    mapping.protocol_element_property = old_value

    @pyqtSlot()
    def on_load_workspace_button_pressed(self):
        path = QFileDialog.getOpenFileName(self, "Load workspace", "", "*.txt")
        log.debug(path)
        if path[0]:
            self.workspace.load(self.saveable_models(), load_from=path[0])

           # except Exception as e:
            #    message_boxes.warning(self, title='Data Not Loaded', text="Could not load {}: {}".format(path[0], e))

    # @pyqtSlot()
    # def on_programStarted(self):
    #     self.protocol_design_widget.stimulus_widget.reset_background()

    @pyqtSlot()
    def on_respiration_monitor_button_pressed(self):
        arduino = self.dependencies.arduino

        # DEBUG FFT
        # self.fft_timer = QTimer()
        # self.fft_timer.timeout.connect(self.debug_fft)
        # self.random_time = 0
        # self.fft_timer.start(50)

        if arduino.is_open():
            arduino.close()
            self.arduino_status_label.setText("Arduino Off")
            arduino.newDataReceived.disconnect(self.temp_func)
            arduino.stop()

        else:
            ports = QSerialPortInfo.availablePorts()
            for port in ports:
                if "Arduino" in port.description():
                    self.respiration_widget.reset()
                    arduino.port = port.portName()
                    arduino.open()
                    self.arduino_status_label.setText("Arduino On ({})".format(port.portName()))
                    self.dependencies.arduino.newDataReceived.connect(self.temp_func)
                    self.dependencies.arduino.start()
                    break

    @pyqtSlot()
    def on_respiration_plot_button_pressed(self):
        self.respiration_widget.show()

    # todo - messy and not good.
    def temp_func(self, line):
       # log.debug(line)
        try:
            string = line.decode()
            data = string.split('\t')
            t = int(data[0])
            # if not hasattr(self, 'arduino_start'):
            #     self.arduino_start = t

            # t = t - self.arduino_start

            y = int(data[1])
        except ValueError:
            pass
        else:
            self.respiration_widget.append(t, y)

    @pyqtSlot(str)
    def on_save_filename_textEdited(self, text):
        self.workspace.filename = text

    @pyqtSlot()
    def on_save_workspace_button_pressed(self):
        self.workspace.save(self.saveable_models())

    def saveable_models(self):
        models = self.dependencies
        return {
            'camera_transform': models.camera_transform,
            'image_stack': models.image_stack,
            'intensity_mask': models.intensity_mask,
            'camera': models.camera,
            'homography_stimulus_window': models.homography_stimulus_window,
            'labjack_states': models.labjack_states,
            'stimulus_points': models.stimulus_points,
            'protocol_sequence': models.protocol_sequence,
        }

    def setup_menuBar(self):
        self.menuBar().addMenu("Help")
        self.menuBar().addMenu("About")

    @pyqtSlot(bool)
    def on_stimulus_window_visibilityChanged(self, visible):
        if visible:
            self.stimulus_window_status.update_status('On')
        else:
            self.stimulus_window_status.update_status('Off')

    def debug_fft(self):
        self.random_time += random.randint(10, 50)
        max_amplitude = 100
        frequency = 2
        amplitude = max_amplitude * sin(2 * pi * frequency * self.random_time / 1000) + \
                    max_amplitude * sin(2 * pi * 4 * frequency * self.random_time / 1000)
        #log.debug("t: {} y: {}".format(self.random_time, amplitude))
        line = "{}\t{}".format(self.random_time, int(amplitude))
        self.temp_func(line.encode())
