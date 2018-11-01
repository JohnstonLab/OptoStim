import logging
import signal
import sys

import asyncio
import quamash
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtWidgets import QApplication

from optostim.application import Application
from optostim.exceptions import OptoStimException
from optostim.optostim_main_window import OptoStimMainWindow
from pyjohnstonlab.devices.exceptions import DeviceException
from pyjohnstonlab.excepthooks import ExceptHook

REQUIRED_PYTHON_VERSION = (3, 6)

# Turn off PyQt5 debug logging as spams the console.
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("PyQt5").setLevel(logging.WARNING)
logging.getLogger("quamash").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

SENTRY_KEY = "https://64b0571cd66b4bf8a971b58a3b927d22:82b8a7aba648402a9a5604b07d77f854@sentry.io/291839"


def main():

    if sys.version_info < REQUIRED_PYTHON_VERSION:
        raise SystemExit("Python {}.{} or higher is required"
                         .format(REQUIRED_PYTHON_VERSION[0], REQUIRED_PYTHON_VERSION[1]))

 #   QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = Application(sys.argv)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)

    pixmap = QPixmap('OptoStimLogo.jpeg')
    splash = QSplashScreen(pixmap)
    splash.show()

    w = OptoStimMainWindow()
    w.show()

    splash.finish(w)

    hook = ExceptHook(sentry_key=SENTRY_KEY, non_exit_exceptions=[DeviceException, OptoStimException])

    sys.excepthook = hook.except_hook

    signal.signal(signal.SIGINT, w.clean_up)
    signal.signal(signal.SIGTERM, w.clean_up)

    try:
        with loop:
            sys.exit(loop.run_forever())
    finally:
        w.clean_up()


if __name__ == "__main__":
    main()


