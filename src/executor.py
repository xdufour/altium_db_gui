from PyQt5 import QtCore
from PyQt5.QtCore import QRunnable, QObject


class Signals(QObject):
    resultAvailable = QtCore.pyqtSignal(object)


class Executor(QRunnable):
    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args
        self.signals = Signals()

    def run(self):
        res = self.fn(*self.args)
        if type(res) == str:
            self.signals.resultAvailable.emit(res)
