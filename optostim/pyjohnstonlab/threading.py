from PyQt5.QtCore import QThread


def create_thread(worker):
    thread = QThread()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)

    worker.finished.connect(thread.quit)

    thread.finished.connect(thread.deleteLater)
    worker.finished.connect(worker.deleteLater)

    return thread