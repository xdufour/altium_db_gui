from PyQt5.QtWidgets import QStatusBar
from enum import Enum


class StatusColor:
    Default = '#adaead'
    Green = '#008355'
    Yellow = '#ecbb06'
    Red = '#cc0000'


class StatusBarLogger:
    statusBar = None

    @staticmethod
    def registerStatusBar(statusBar: 'QStatusBar'):
        StatusBarLogger.statusBar = statusBar

    @staticmethod
    def setStatus(message, color):
        StatusBarLogger.statusBar.showMessage(message)
        StatusBarLogger.statusBar.setStyleSheet(f'font-size: 9pt; color: {color};')
        StatusBarLogger.statusBar.style().unpolish(StatusBarLogger.statusBar)
        StatusBarLogger.statusBar.style().polish(StatusBarLogger.statusBar)
        StatusBarLogger.statusBar.repaint()
        StatusBarLogger.statusBar.show()
