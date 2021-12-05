from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QObject, QEvent
from PyQt5 import QtCore


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

    mousePressed = QtCore.pyqtSignal()

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.MouseButtonPress:
            self.mousePressed.emit()
            return True
        return super(MainWindow, self).eventFilter(obj, event)
