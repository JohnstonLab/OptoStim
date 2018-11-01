import logging
import traceback
import sys

from PyQt5.QtWidgets import QMessageBox

from optostim.exceptions import OptoStimException


def optostim_excepthook(exception, value, traceback_object):

    if exception == KeyboardInterrupt:
        sys.exit(0)

    is_optostim_error = isinstance(value, OptoStimException)

    logging.error(
        "Uncaught exception",
        exc_info=(exception, value, traceback_object)
    )
    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Critical)

    window_title = "OptoStim Exception" if is_optostim_error else "Uncaught Exception"
    message_box.setWindowTitle(window_title)

    text = 'Type: {}\n'.format(exception)
    text += 'Value: {}\n'.format(value)
    text += 'Traceback:\n{}'.format(traceback.format_tb(traceback_object))

    message_box.setText(text)
    message_box.exec_()

    if not is_optostim_error:
        sys.exit(-1)