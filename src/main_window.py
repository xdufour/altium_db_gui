from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QObject, QEvent
from PyQt5 import QtCore


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

    mousePressed = QtCore.pyqtSignal(str)

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        if event.type() == QEvent.MouseButtonPress and obj.isWidgetType():
            self.mousePressed.emit(obj.objectName())
            return False
        return super(MainWindow, self).eventFilter(obj, event)
