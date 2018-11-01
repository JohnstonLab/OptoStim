import logging
import sys
import traceback

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMessageBox
from raven import Client

from pyjohnstonlab.devices.exceptions import DeviceException


log = logging.getLogger(__name__)


def report_sent_message_box():
    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Information)

    window_title = "Report Sent"
    message_box.setWindowTitle(window_title)

    text = 'Report sent. Abort application or try to continue?'

    message_box.setText(text)
    report_button = message_box.addButton("Try to continue", QMessageBox.AcceptRole)
    abort_button = message_box.addButton("Exit", QMessageBox.DestructiveRole)

    message_box.exec_()

    if message_box.clickedButton() == abort_button:
        log.info("Aborting")
        QCoreApplication.quit()


def handle_fatal_exception(sentry_client, exception, value, traceback_object):
    logging.error(
        "Uncaught exception",
        exc_info=(exception, value, traceback_object)
    )

    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Critical)

    window_title = "Unhandled Exception"
    message_box.setWindowTitle(window_title)

    text = 'Type: {}\n'.format(exception)
    text += 'Value: {}\n'.format(value)
    text += 'Traceback:\n{}'.format(traceback.format_tb(traceback_object))

    message_box.setText(text)

    try_to_continue_button = message_box.addButton("Try to continue", QMessageBox.AcceptRole)
    report_button = message_box.addButton("Send Report", QMessageBox.AcceptRole)
    abort_button = message_box.addButton("Abort", QMessageBox.DestructiveRole)
    message_box.exec_()
    #
    if message_box.clickedButton() == abort_button:
        log.info("Aborting")
        QCoreApplication.quit()
    elif message_box.clickedButton() == report_button:
        sentry_client.captureException(exc_info=(exception, value, traceback_object))
        report_sent_message_box()


def handle_non_except_exception(exception, value, traceback_object):
    logging.warning(value)
    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Warning)
    message_box.setWindowTitle("OptoStim Warning")
    message_box.setText("{}".format(value))
    message_box.exec_()


class ExceptHook:

    def __init__(self, sentry_key='', non_exit_exceptions=None):
        self.non_exit_exceptions = non_exit_exceptions
        self.client = Client(sentry_key)

    def except_hook(self, exception, value, traceback_object):

        if exception == KeyboardInterrupt:
            sys.exit(0)

        if exception in self.non_exit_exceptions:
            handle_non_except_exception(exception, value, traceback_object)
        else:
            handle_fatal_exception(self.client, exception, value, traceback_object)


def basic_excepthook(exception, value, traceback_object):

    if exception == KeyboardInterrupt:
        sys.exit(0)

    logging.error(
        "Uncaught exception",
        exc_info=(exception, value, traceback_object)
    )

    message_box = QMessageBox()
    message_box.setIcon(QMessageBox.Critical)

    window_title = "Unhandled Exception"
    message_box.setWindowTitle(window_title)

    text = 'Type: {}\n'.format(exception)
    text += 'Value: {}\n'.format(value)
    text += 'Traceback:\n{}'.format(traceback.format_tb(traceback_object))

    message_box.setText(text)
    message_box.exec_()

    if exception not in (DeviceException,):
        sys.exit(-1)
