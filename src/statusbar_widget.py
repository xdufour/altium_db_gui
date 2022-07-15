from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout


class StatusColor:
    Default = '#adaead'
    Green = '#16a349'
    Yellow = '#b08946'
    Red = '#c75450'


class StatusBar(QWidget):
    def __init__(self, textHeight):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.gridLayout)

        self.lightSpaceWidget = QWidget()
        self.darkSpaceWidget = QWidget()

        self.lightSpaceWidget.setProperty('mainWindow', True)
        self.gridLayout.addWidget(self.lightSpaceWidget, 0, 0)
        self.statusBarMessage = QLabel('')
        self.gridLayout.addWidget(self.statusBarMessage, 0, 2)
        self.gridLayout.setSpacing(0)
        self.gridLayout.addWidget(self.darkSpaceWidget, 0, 1)
        self.gridLayout.setColumnMinimumWidth(1, int(textHeight * 0.7))
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setRowMinimumHeight(0, int(textHeight * 1.6))
        self.hide()

    def setStatus(self, message, color=StatusColor.Default):
        self.statusBarMessage.setText(message)
        self.statusBarMessage.setStyleSheet(f'font-size: 9pt; color: {color};')
        self.statusBarMessage.style().unpolish(self.statusBarMessage)
        self.statusBarMessage.style().polish(self.statusBarMessage)
        self.statusBarMessage.repaint()
        self.setVisible(len(message) > 0)

    def setOffsetWidth(self, w):
        self.lightSpaceWidget.setMinimumWidth(w)