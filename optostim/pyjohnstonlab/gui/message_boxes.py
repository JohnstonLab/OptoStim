from PyQt5.QtWidgets import QMessageBox


def information(parent, title, text):

    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.exec_()


def question(parent, title, text):

    reply = QMessageBox.question(parent, title, text, QMessageBox.Yes | QMessageBox.No)

    if reply == QMessageBox.Yes:
        return True
    else:
        return False


def warning(parent, title, text):

    message_box = QMessageBox(parent)
    message_box.setIcon(QMessageBox.Warning)

    message_box.setWindowTitle(title)
    message_box.setText(text)
    message_box.exec_()