from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QGroupBox, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QFont
import sys
import breeze_resources
import utils


def main():
    app = QApplication(sys.argv)

    appIcon = utils.loadQIcon('assets/app.ico')
    homeIcon = utils.loadQIcon('assets/home_rotated.png')
    settingsIcon = utils.loadQIcon('assets/settings_rotated.png')

    app.setApplicationDisplayName("Altium DB GUI")
    app.setWindowIcon(appIcon)

    app.setFont(QFont('Arial', 11))

    # set stylesheet
    file = QFile(":/dark/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())

    # code goes here
    tabWidget = QTabWidget()
    tabWidget.setMinimumSize(1920, 1080)
    tabWidget.setTabPosition(QTabWidget.West)

    homeWidget = QWidget()
    settingsWidget = QWidget()

    tabWidget.addTab(homeWidget, '')
    tabWidget.setTabIcon(0, homeIcon)
    tabWidget.addTab(settingsWidget, '')
    tabWidget.setTabIcon(1, settingsIcon)
    tabWidget.setIconSize(QtCore.QSize(64, 64))
    tabWidget.show()

    # Settings page widgets
    settingsVLayout = QVBoxLayout()
    settingsTopHLayout = QHBoxLayout()
    settingsWidget.setLayout(settingsVLayout)
    settingsVLayout.addLayout(settingsTopHLayout)
    settingsVLayout.addStretch(1)

    loginGroupBox = QGroupBox("MySQL Server Login")
    loginGroupBox.setAlignment(Qt.AlignLeft)
    settingsTopHLayout.addWidget(loginGroupBox, 0)
    settingsTopHLayout.addStretch(1)
    loginGridLayout = QGridLayout()
    loginGroupBox.setLayout(loginGridLayout)
    loginGridLayout.setColumnMinimumWidth(1, 50)
    loginGridLayout.setSpacing(20)

    dbAddressLabel = QLabel("Address:")
    dbAddressLineEdit = QLineEdit()
    loginGridLayout.addWidget(dbAddressLabel, 0, 0)
    loginGridLayout.addWidget(dbAddressLineEdit, 0, 2)

    dbUserLabel = QLabel("User:")
    dbUserLineEdit = QLineEdit()
    loginGridLayout.addWidget(dbUserLabel, 1, 0)
    loginGridLayout.addWidget(dbUserLineEdit, 1, 2)

    dbPasswordLabel = QLabel("Password:")
    dbPasswordLineEdit = QLineEdit()
    loginGridLayout.addWidget(dbPasswordLabel, 2, 0)
    loginGridLayout.addWidget(dbPasswordLineEdit, 2, 2)

    dbNameLabel = QLabel("Database:")
    dbNameLineEdit = QLineEdit()
    loginGridLayout.addWidget(dbNameLabel, 3, 0)
    loginGridLayout.addWidget(dbNameLineEdit, 3, 2)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()