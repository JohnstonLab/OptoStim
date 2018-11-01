import asyncio
import logging

import serial
import serial_asyncio
from PyQt5.QtCore import QTimer, pyqtSignal

from pyjohnstonlab.devices.device import Device
from pyjohnstonlab.devices.exceptions import DeviceException

log = logging.getLogger(__name__)


class ArduinoDevice(Device):

    connectionLost = pyqtSignal()
    connectionMade = pyqtSignal()
    newDataReceived = pyqtSignal(bytes)

    def __init__(self, port=None, parent=None):
        super().__init__(parent)

        self._ser = serial.Serial()

        self._timer = QTimer()
        self._interval = 5
        self._timer.setInterval(self._interval)
        self._timer.timeout.connect(self._query_arduino)
        self.iter = 1

    def _query_arduino(self):
        #log.debug("arduino tick")
       # lines = b""
        if self._ser.in_waiting > 0:
            try:
                lines = self._ser.readline()
            except serial.serialutil.SerialException as error:
                log.warning(error)
            else:
                if lines:
                    self.newDataReceived.emit(lines)

    def _query_connection(self):
        pass

    def _try_command(self, command, *args):
        try:
            func = getattr(self._ser, command, None)
        except AttributeError as error:
            raise DeviceException(error)

        try:
            return func(*args)
        except serial.serialutil.SerialException as error:
            raise DeviceException(error)

    def flush_output(self):
        self._ser.reset_output_buffer()

    def get_serial(self):
        return self._ser

    def is_open(self):
        return self._ser.is_open

    def open(self):
        self._try_command('open')

    @property
    def port(self):
        return self._ser.port

    @port.setter
    def port(self, new_port):
        self._ser.port = new_port

    def readline(self):
        line = ""
        if self._ser.inWaiting() > 0:
            try:
                line = self._ser.readlines()
            except serial.serialutil.SerialException as error:
                log.warning(error)
        return line

    def close(self):
        self._ser.close()

    def stop(self):
        self._timer.stop()
        self.close()

    def start(self):
        self._ser.reset_output_buffer()
        self._timer.start()


class Output(asyncio.Protocol):

    def __init__(self):
        self.connected = False
        self.device = None

    def connection_made(self, transport):
        self.transport = transport
        self.connected = True
        self.device.connectionMade.emit()
        log.debug("connection made")

    def connection_lost(self, exc):
        log.debug("connection lost")
        self.transport.loop.stop()
        self.connected = False
        self.device.connectionLost.emit()

    def data_received(self, data):
        self.device.newDataReceived.emit(data)

    def pause_writing(self):
        log.debug("pause writing")

    def resume_writing(self):
        log.debug("resume writing")

#  todo - odd results when using async arduino. Does not match synchronous 
class ArduinoDeviceAsync(ArduinoDevice):

    def __init__(self):
        super().__init__()
        self.protocol = None
        self.transport = None

    def close(self):
        self.transport.close()

    def is_open(self):
        if self.transport and self.transport.serial:
            return self.transport.serial.is_open
        else:
            return False

    def open(self):
        loop = asyncio.get_event_loop()
        coroutine = serial_asyncio.create_serial_connection(loop, Output, self.port)
        try:
            self.transport, self.protocol = loop.run_until_complete(coroutine)

        except serial.serialutil.SerialException as e:
            raise DeviceException(e)
        else:
            self.protocol.device = self
            self._ser = self.transport.serial

    def stop(self):
        self.transport.loop.stop()

