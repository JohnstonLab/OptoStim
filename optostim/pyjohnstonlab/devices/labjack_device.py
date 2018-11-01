import logging
from time import sleep

import LabJackPython
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import u3

from pyjohnstonlab.devices.exceptions import DeviceException

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

DEVICE_CHECK_INTERVAL = 1000

FIO4 = u3.FIO4
FIO5 = u3.FIO5
FIO6 = u3.FIO6
FIO7 = u3.FIO7

FIO_STATES = [FIO4, FIO5, FIO6, FIO7]

DAC0_REGISTER = 5000
DAC1_REGISTER = 5002

LOW = 0
HIGH = 1

WAIT_FOR_SIGNAL_SLEEP = 0.1


class LabJackControl:

    def __init__(self, label):
        self.label = label


class FIOState(QObject):

    labelChanged = pyqtSignal(str)

    def __init__(self, number, label="", parent=None):
        super().__init__(parent)
        self.number = number
        self._label = label

    def __repr__(self):
        return "fio{} (label: {})".format(self.number, self.label)

    @property
    def label(self):
        return self._label if self._label else "FIO{}".format(self.number)

    @label.setter
    def label(self, new_label):
        if new_label != self._label:
            self._label = new_label
            self.labelChanged.emit(self._label)


class DACState(FIOState):

    @property
    def label(self):
        return self._label if self._label else "DAC{}".format(self.number)


class LabJackDevice(QObject):

    default = [False, False, False, False, 0.0, 0.0, 0.0]
    disconnected = pyqtSignal()
    connected = pyqtSignal()
    fio_numbers = [4, 5, 6, 7]
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self._device = None
        self._status = ""
        self._is_connected = False

        self.controls = []
        self.dacs = []
        self.fios = []

        for fio_num in FIO_STATES:
            name = 'fio{}'.format(fio_num)
            label = kwargs.get(name + "_label", "")
            setattr(self, name, FIOState(number=fio_num, label=label))
            self.fios.append(getattr(self, name))
            self.controls.append(self.fios[-1])

        name = "DAC0"
        label = kwargs.get("DAC0_label", "")
        setattr(self, name, DACState(number=0, label=label))
        self.dacs.append(getattr(self, name))
        self.controls.append(self.dacs[-1])

        name = "DAC1"
        label = kwargs.get("DAC1_label", "")
        setattr(self, name, DACState(number=1, label=label))
        self.dacs.append(getattr(self, name))
        self.controls.append(self.dacs[-1])

        self._device_check_timer = QTimer()
        self._device_check_timer.setInterval(DEVICE_CHECK_INTERVAL)
        self._device_check_timer.timeout.connect(self._check_device)
        self._device_check_timer.start()

    def __del__(self):
        self.close()

    def _check_device(self):
        log.debug("Checking labjack")
        device = self._get_device()
        if device and not self._device:
            self._device = device
            self.clear()
            self.connected.emit()
        elif self._device and not device:
            self._device = None
            self.disconnected.emit()

    def _get_device(self):
        device = None
        try:
            device = u3.U3()
        except LabJackPython.LabJackException as e:
            self.status = e.errorString
        else:
            self.status = "OK"
        return device

    def _try_command(self, command, *args, **kwargs):
        if self._device:
            function = getattr(self._device, command)
            try:
                return function(*args, **kwargs)
            except LabJackPython.LabJackException as error:
                raise DeviceException(error)

    def available(self):
        return True if self._device else False

    @property
    def check_device(self):
        return self._device_check_timer.isActive()

    @check_device.setter
    def check_device(self, do_check):
        if do_check:
            log.info("Starting periodic labjack device check.")
            self._device_check_timer.start()
        else:
            log.info("Stopping periodic labjack device check")
            self._device_check_timer.stop()

    @property
    def is_connected(self):
        return True if self._device else False

    def clear(self):
        if not self._device:
            raise DeviceException(self.status)
        [self._device.setFIOState(number, LOW) for number in self.fio_numbers]

        self.set_DAC0(0.0)
        self.set_DAC1(0.0)

    def close(self):
        if self._device:
            log.info("Closing LabJack device.")
            self._device.close()

    def execute_command_list(self, command):
        self._device.getFeedback(command)

    def generate_command_lists(self, states):
        command_lists = []
        previous_state = self.default
        for state in states:
            command_list = []
            #  FIOs
            for i in range(4, 8):
                if previous_state[i - 4] != state[i - 4]:
                    command_list.append(u3.BitStateWrite(i, state[i - 4]))

            # DACs
            if previous_state[4] != state[4]:
                voltage_in_bits = self._device.voltageToDACBits(volts=state[4], dacNumber=0)
                command_list.append(u3.DAC0_8(voltage_in_bits))

            if previous_state[5] != state[5]:
                voltage_in_bits = self._device.voltageToDACBits(volts=state[5], dacNumber=1)
                command_list.append(u3.DAC1_8(voltage_in_bits))

            command_lists.append(command_list)
            previous_state = state
        return command_lists

    def label(self, i):
        if 0 <= i < len(self.fios):
            return self.fios[i].label
        elif i == 4:
            return self.dacs[0].label
        elif i == 5:
            return self.dacs[1].label
        elif i == 6:
            return 'Duration'
        raise IndexError

    def labels(self):
        labels = [fio.label for fio in self.fios]
        labels.append('DAC0')
        labels.append('DAC1')
        labels.append('Duration')
        return labels

    def set_DAC0(self, voltage):
        voltage_in_bits = self._device.voltageToDACBits(volts=voltage, dacNumber=0)
        return self._try_command('getFeedback', u3.DAC0_8(voltage_in_bits))

    def set_DAC1(self, voltage):
        voltage_in_bits = self._device.voltageToDACBits(volts=voltage, dacNumber=1)
        self._try_command('getFeedback', u3.DAC1_8(voltage_in_bits))

    def set_fio_state(self, number, state):
        self._try_command('setFIOState', number, state)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        self._status = new_status
        self.status_changed.emit(self._status)

    def wait_for_signal(self, io_number):
        # or getAIN(channel) ?
        while self._device.getDIState(io_number) == HIGH:
            sleep(WAIT_FOR_SIGNAL_SLEEP)


