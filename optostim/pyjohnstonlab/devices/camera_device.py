import logging

import cv2
import numpy as np
import os
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from pyjohnstonlab.devices.exceptions import DeviceException
from pyjohnstonlab.mixins import JSONPickleMixin
from pyjohnstonlab.thirdparty.mmcorepy import MMCorePy

log = logging.getLogger(__name__)

MAX_EXPOSURE = 2000

EXPOSURE = 'Exposure'
GAIN = 'Gain'


class CameraProperty(QObject):

    valueChanged = pyqtSignal()

    def __init__(self, camera, allowed_values, has_limits, name, min_value, max_value, read_only):
        super().__init__(camera)
        self.allowed_values = allowed_values
        self.camera = camera
        self.has_limits = has_limits
        self.name = name
        self.min = min_value
        self.max = max_value
        self.read_only = read_only

        self.type = str

        if not read_only and not allowed_values:
            self.type = float
            self.min = float(min_value)
            self.max = float(max_value)

    def __repr__(self):
        return "Property {}".format(self.name)

    @property
    def current(self):
        value = self.camera.get_property(self.name)
        try:
            converted = self.type(value)
        except ValueError:
            converted = 0.0
        return converted

    @current.setter
    def current(self, new_value):
        if new_value != self.current:
            self.camera.set_property(self.name, new_value)
            self.valueChanged.emit()


class CameraDevice(QObject):

    module = None
    device_name = None
    _mmc = None

    homographyMatrixChanged = pyqtSignal(np.ndarray)
    newFrameReceived = pyqtSignal(np.ndarray)
    initialised = pyqtSignal()
    device_disconnected = pyqtSignal()
    exposure_changed = pyqtSignal(float)
    gainChanged = pyqtSignal(float)

    def __init__(self, interval=250, parent=None):
        super().__init__(parent)
        self._homography_matrix = np.identity(3)
        self._initialised = False
        self.last_error = ""
        self.last_image = None
        self.device_label = 'Camera'
        self._interval = interval
        self.properties = []
        self.properties_dict = {}
        self.use_homography_matrix = False

        self._gain_name = ''
        self._timer = QTimer()
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._query_frame)

        if not self._mmc:
            self._mmc = MMCorePy.CMMCore()

    def __getstate__(self):
        return {'homography_matrix': pd.DataFrame(self._homography_matrix).to_json()}

    def __setstate__(self, state):
        self.homography_matrix = pd.read_json(state['homography_matrix']).values


    @property
    def exposure(self):
        return self._mmc.getExposure()

    @exposure.setter
    def exposure(self, new_exposure):
        if new_exposure != self.exposure:
            self._mmc.setExposure(new_exposure)
            self.exposure_changed.emit(self.exposure)

    @property
    def homography_matrix(self):
        return self._homography_matrix

    @homography_matrix.setter
    def homography_matrix(self, new_matrix):
        self._homography_matrix = new_matrix
        self.homographyMatrixChanged.emit(self._homography_matrix)

    @property
    def gain(self):
        return float(self.get_property(self.gain_name))

    @gain.setter
    def gain(self, new_gain):
        if new_gain != self.gain:
            self.set_property(self.gain_name, new_gain)
            self.gainChanged.emit(self.gain)

    @property
    def gain_name(self):
        return self._gain_name

    def _find_gain_property_name(self):
        gain = GAIN
        if gain not in self.properties_dict:
            for key, value in self.properties_dict.items():
                if key.lower().find('gain') == 0:
                    gain = key
                    break
        return gain

    def _problem_with_device(self):
        self.initialised = False
        self.device_disconnected.emit()
#        self._device_check_timer.start()

    def _try_initialise(self):

        if self.initialised:
            return

        try:
            self._mmc.initializeDevice(self.device_label)
        except MMCorePy.CMMError as error:
            raise DeviceException(error)
        else:
            log.debug("Device {} can initialise.".format(self.device_name))
            self._device_check_timer.stop()
            self.initialised = True
            self.device_initialised.emit()
            self._setup_device()

    def _try_command(self, command, *args):
        try:
            func = getattr(self._mmc, command, None)
        except AttributeError as error:
            raise DeviceException(error)

        try:
            return func(*args)
        except MMCorePy.CMMError as error:
            raise DeviceException(error)

    def _query_frame(self):
       # log.debug('query frame')
        frame = None
        try:
            if self._mmc.getRemainingImageCount() > 0:
                frame = self._mmc.getLastImage()
        except Exception as error:
            log.warning(error)
            raise DeviceException(error)
        else:
            if frame is not None:
                if self.use_homography_matrix:
                    self.last_image = cv2.warpPerspective(frame, self.homography_matrix, (1024, 1024))
                else:
                    self.last_image = frame
                self.newFrameReceived.emit(self.last_image)

    def available_adapters(self):
        return self._mmc.getDeviceAdapterNames()

    def get_available_device(self, library):
        return self._try_command('getAvailableDevices', library)
        #return self._mmc.getAvailableDevices(library)

    def get_device_adapter_names(self):
        return self._mmc.getDeviceAdapterNames()

    def get_device_property_names(self):
        return self._mmc.getDevicePropertyNames(self.device_label)

    def get_image(self):
        return self._mmc.getImage() #self._try_command('getImage')

    def get_property(self, property_name):
        return self._try_command('getProperty', self.device_label, property_name)

    def initialise(self, adapter, device):
        try:
            self._mmc.unloadAllDevices()
            self._mmc.loadDevice(self.device_label, adapter, device)
            self._mmc.initializeDevice(self.device_label)
            self._mmc.setCameraDevice(self.device_label)
        except MMCorePy.CMMError as error:
            self._mmc.unloadAllDevices()
            raise DeviceException(error)

        self.properties.clear()
        self.properties_dict.clear()
        property_names = self._mmc.getDevicePropertyNames(self.device_label)

        for property in property_names:
            args = (self.device_label, property)
            allowed_values = self._mmc.getAllowedPropertyValues(*args)
            current = self._mmc.getProperty(self.device_label, property)
            min = self._mmc.getPropertyLowerLimit(self.device_label, property)
            max = self._mmc.getPropertyUpperLimit(self.device_label, property)
            read_only = self._mmc.isPropertyReadOnly(self.device_label, property)
            has_limits = self._mmc.hasPropertyLimits(self.device_label, property)
            #log.debug("Property: {}, Read only: {}, limits: {}, allowed values = {}"
            #          .format(property, read_only, has_limits, allowed_values))
            cam_property = CameraProperty(allowed_values=allowed_values,
                                          camera=self,
                                          has_limits=has_limits,
                                          name=property,
                                          min_value=min,
                                          max_value=max,
                                          read_only=read_only)
            self.properties.append(cam_property)
            self.properties_dict[cam_property.name] = cam_property

        self._gain_name = self._find_gain_property_name()
        self.initialised.emit()

    def reset(self):
        log.debug("Resetting camera {} {}".format(self.module, self.device_name))
        self._mmc.reset()

    def snap_image(self):
        self._mmc.snapImage()
       # self._try_command('snapImage')

    def set_property(self, name, value):
        self._try_command('setProperty', self.device_label, name, value)
        if name == EXPOSURE:
            self.exposure_changed.emit(self.exposure)
        elif name == self.gain_name:
            self.gainChanged.emit(self.gain)

    def set_roi(self, x, y, width, height):
        self._try_command('setROI', x, y, width, height)

    def start_acquisition(self):
        try:
            if not self._timer.isActive():
                #self.stop_acquisition()
                self._mmc.startContinuousSequenceAcquisition(self._interval)
            else:
                log.info("Camera is already acquiring.")
        except MMCorePy.CMMError as error:
            raise DeviceException(error)
        else:
            self._timer.start()
            log.debug("Camera on")

    def stop_acquisition(self):
        num_frame_subscribers = self.receivers(self.newFrameReceived)
        log.debug("Number of frame subscribers: {}".format(num_frame_subscribers))

        if num_frame_subscribers < 2:
            self._timer.stop()
            self._mmc.stopSequenceAcquisition()
            log.debug("Camera off")
        else:
            log.info("Can not stop acquisition. Other objects are subscribed.")

    def unload(self):
        try:
            self.stop_acquisition()
        except MMCorePy.CMMError:
            log.info("Camera not loaded or initialised. No need to stop acquisition and unload.")
        else:
            log.debug("Unloading module:{}, device name: {}".format(self.module, self.device_name))
            self._try_command('unloadDevice', self.device_label)



