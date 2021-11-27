from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,\
    QGroupBox, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget, QFileDialog, QDialog
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QFile, QTextStream, QSize, QRect
from PyQt5.QtGui import QFont, QFontMetrics
import numpy as np
import sys
import glob
import breeze_resources
import utils
import json_appdata
import mysql_query
import mysql
import altium_parser
import dk_api

permanentParams = ["Name", "Supplier 1", "Supplier Part Number 1", "Library Path",
                   "Library Ref", "Footprint Path", "Footprint Ref"]

labels = {}
lineEdits = {}

def getDbTableList(mysql_cnx):
    dbTableList = []
    dbTableCursor = mysql_query.getDatabaseTables(mysql_cnx)
    for it in dbTableCursor:
        dbTableList.append(it[0])
    return dbTableList


class App:
    def __init__(self):
        app = QApplication(sys.argv)

        appIcon = utils.loadQIcon('assets/app.ico')
        homeIcon = utils.loadQIcon('assets/home_rotated.png')
        settingsIcon = utils.loadQIcon('assets/settings_rotated.png')
        downloadIcon = utils.loadQIcon('assets/download_cloud.png')

        app.setApplicationDisplayName("Altium DB GUI")
        app.setWindowIcon(appIcon)

        app.setFont(QFont('Arial', 11))

        self.connected = False
        self.loginInfoDict = {}

        self.loginInfoDict = {
            "address": "",
            "user": "",
            "password": "",
            "database": ""
        }

        self.connected = False
        self.dbTableList = []
        self.dbColumnNames = []

        def loadGUI(componentName):
            updateCreateComponentFrame()
            updateTableViewFrame()
            print(f"Loaded GUI for {componentName}")

        def updateCreateComponentFrame():
            row = 2
            dbColumnListCursor = mysql_query.getTableColumns(self.cnx, tableNameCombobox.currentText())
            # Delete any previously created widgets
            for k in labels:
                labels[k].deleteLater()
            labels.clear()
            for k in lineEdits:
                lineEdits[k].deleteLater()
            lineEdits.clear()
            self.dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnListCursor):
                self.dbColumnNames.append(column[0])
                if self.dbColumnNames[i] not in permanentParams:
                    label = QLabel(self.dbColumnNames[i] + ":")
                    labels[self.dbColumnNames[i].lower()] = label
                    lineEdit = QLineEdit()
                    lineEdits[self.dbColumnNames[i].lower()] = lineEdit
                    componentEditorGridLayout.addWidget(label, row, 0)
                    componentEditorGridLayout.addWidget(lineEdit, row, 1)
                    row += 1

        def updateTableViewFrame():
            dbDataCursor = mysql_query.getTableData(self.cnx, tableNameCombobox.currentText())
            data = dbDataCursor.fetchall()

            tableWidget.setSortingEnabled(False)
            tableWidget.clear()
            tableWidget.setColumnCount(len(self.dbColumnNames))
            tableWidget.setRowCount(len(data))
            tableWidget.setHorizontalHeaderLabels(self.dbColumnNames)

            fm = QFontMetrics(QFont('Arial', 9))
            maxColumnWidth = 500
            widthPadding = 40
            cellWidths = []

            for row, cellData in enumerate(data):
                rowWidths = []
                for column, cellData in enumerate(cellData):
                    item = QTableWidgetItem(str(cellData))
                    tableWidget.setItem(row, column, item)
                    rowWidths.append(fm.boundingRect(str(cellData)).width() + widthPadding)
                cellWidths.append(rowWidths)

            for i in range(len(self.dbColumnNames)):
                headerWidth = fm.boundingRect(self.dbColumnNames[i]).width() + widthPadding
                dataWidth = utils.columnMax(cellWidths, i)
                tableWidget.setColumnWidth(i, max([min(headerWidth, maxColumnWidth), min(dataWidth, maxColumnWidth)]))

            tableWidget.setSortingEnabled(True)

        def query_supplier():
            dkpn = ceSupplierPnLineEdit.text()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, tableNameCombobox.currentText(), utils.strippedList(self.dbColumnNames, permanentParams))
            for columnName, value in result:
                try:
                    lineEdits[columnName.lower()].setText(value)
                    lineEdits[columnName.lower()].setCursorPosition(0)
                except KeyError:
                    print(f"Error: no field found for \'{columnName.lower()}\'")

        def addToDatabaseClicked():
            rowData = []
            for col in self.dbColumnNames:
                try:
                    rowData.append(QLineEdit(lineEdits[col.lower()]).text())
                except KeyError:
                    print(f"Error: No field found for \'{col.lower()}\'")
                    return
            mysql_query.insertInDatabase(self.cnx, tableNameCombobox.currentText(), self.dbColumnNames, rowData)

        def validateName(name):
            ceAddButton.setEnabled(len(name) > 0)

        def loadDbTables():
            self.dbTableList = getDbTableList(self.cnx)
            tableNameCombobox.addItems(self.dbTableList)

        def loadDbLogins():
            self.loginInfoDict = json_appdata.getDatabaseLoginInfo()
            dbAddressLineEdit.insert(self.loginInfoDict['address'])
            dbUserLineEdit.insert(self.loginInfoDict['user'])
            dbPasswordLineEdit.insert(self.loginInfoDict['password'])
            dbNameLineEdit.insert(self.loginInfoDict['database'])

        def saveDbLogins():
            json_appdata.saveDatabaseLoginInfo(dbAddressLineEdit.text(),
                                               dbUserLineEdit.text(),
                                               dbPasswordLineEdit.text(),
                                               dbNameLineEdit.text())

        def testDbConnection():
            if not self.connected and not utils.dictHasEmptyValue(self.loginInfoDict):
                try:
                    self.cnx = mysql_query.init(dbUserLineEdit.text(),
                                                dbPasswordLineEdit.text(),
                                                dbAddressLineEdit.text(),
                                                dbNameLineEdit.text())
                    if self.cnx.is_connected:
                        self.connected = True
                        print("Connected to database successfully")
                        loadDbTables()
                        dbTestButton.setDisabled(True)
                        dbTestButton.setText("Connected")
                        loginGroupBox.setProperty('valid', True)
                        loginGroupBox.style().unpolish(loginGroupBox)
                        loginGroupBox.style().polish(loginGroupBox)
                        tabWidget.setTabEnabled(0, True)
                except mysql.connector.errors.ProgrammingError:
                    print("Access Denied")
                except mysql.connector.errors.InterfaceError:
                    print("Invalid Login Information Format")
            if not self.connected:
                tabWidget.setTabEnabled(0, False)

        def browseBtn():
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.DirectoryOnly)
            if dialog.exec_() == QDialog.Accepted:
                directory = dialog.selectedFiles()[0]
                updateSearchPath(directory)
                json_appdata.saveLibrarySearchPath(directory)

        def getLibSearchPath():
            self.searchPathDict = json_appdata.getLibrarySearchPath()
            if 'filepath' in self.searchPathDict:
                updateSearchPath(self.searchPathDict['filepath'])

        def updateSearchPath(path):
            searchPathLineEdit.setText(path)
            print(f"Library search path set: {path}")
            updatePathComboboxes(path)

        def updatePathComboboxes(dirPath):
            schlibFiles = glob.glob(dirPath + '/**/*.SchLib', recursive=True)
            pcblibFiles = glob.glob(dirPath + '/**/*.PcbLib', recursive=True)
            ceLibraryPathCombobox.clear()
            ceFootprintPathCombobox.clear()
            for f in schlibFiles:
                ceLibraryPathCombobox.addItem(f[f.find('Symbols'):].replace('\\', '/', 255))
            for f in pcblibFiles:
                ceFootprintPathCombobox.addItem(f[f.find('Footprints'):].replace('\\', '/', 255))

        def updateLibraryRefCombobox():
            ceLibraryRefCombobox.clear()
            ceLibraryRefCombobox.addItems(altium_parser.getLibraryRefList(
                searchPathLineEdit.text() + '/' + ceLibraryPathCombobox.currentText()))

        def updateFootprintRefCombobox():
            ceFootprintRefCombobox.clear()
            ceFootprintRefCombobox.addItems(altium_parser.getFootprintRefList(
                searchPathLineEdit.text() + '/' + ceFootprintPathCombobox.currentText()))

        # set stylesheet
        file = QFile(":/dark/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)

        mainWindow = QWidget()
        mainWindow.setProperty('mainWindow', True)
        mainWindow.setMinimumSize(1920, 1080)
        mainWindow.resize(1920, 1440)
        mainWindow.setLayout(mainLayout)

        tabWidget = QTabWidget()
        tabWidget.setTabPosition(QTabWidget.West)
        mainLayout.addWidget(tabWidget)

        homeWidget = QWidget()
        settingsWidget = QWidget()

        tabWidget.addTab(homeWidget, '')
        tabWidget.setTabIcon(0, homeIcon)
        tabWidget.addTab(settingsWidget, '')
        tabWidget.setTabIcon(1, settingsIcon)
        tabWidget.setIconSize(QtCore.QSize(64, 64))

        # Settings page widgets
        settingsVLayout = QVBoxLayout()
        settingsTopHLayout = QHBoxLayout()
        settingsWidget.setLayout(settingsVLayout)
        settingsVLayout.addLayout(settingsTopHLayout)
        settingsVLayout.addStretch(1)

        loginGroupBox = QGroupBox("MySQL Server Login")
        loginGroupBox.setAlignment(Qt.AlignLeft)

        settingsTopHLayout.addWidget(loginGroupBox, 0)
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
        dbPasswordLineEdit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        loginGridLayout.addWidget(dbPasswordLabel, 2, 0)
        loginGridLayout.addWidget(dbPasswordLineEdit, 2, 2)

        dbNameLabel = QLabel("Database:")
        dbNameLineEdit = QLineEdit()
        loginGridLayout.addWidget(dbNameLabel, 3, 0)
        loginGridLayout.addWidget(dbNameLineEdit, 3, 2)

        dbTestButton = QPushButton("Test")
        loginGridLayout.addWidget(dbTestButton, 4, 0, 1, 2)
        dbTestButton.released.connect(testDbConnection)

        dbSaveButton = QPushButton("Save")
        loginGridLayout.addWidget(dbSaveButton, 4, 2)
        dbSaveButton.released.connect(saveDbLogins)

        settingsTopRightVLayout = QVBoxLayout()
        searchPathHLayout = QHBoxLayout()
        settingsTopHLayout.addLayout(settingsTopRightVLayout, 1)
        settingsTopRightVLayout.addLayout(searchPathHLayout)
        settingsTopRightVLayout.addStretch(1)
        searchPathLabel = QLabel("Library Search Path:")
        searchPathHLayout.addWidget(searchPathLabel, 0, Qt.AlignLeft)
        searchPathLineEdit = QLineEdit()
        searchPathHLayout.addWidget(searchPathLineEdit, 1)
        searchPathButton = QPushButton("Browse")
        searchPathButton.released.connect(browseBtn)
        searchPathHLayout.addWidget(searchPathButton)

        # Home page widgets
        homeVLayout = QVBoxLayout()
        homeWidget.setLayout(homeVLayout)

        hometopHLayout = QHBoxLayout()
        homeVLayout.addLayout(hometopHLayout)

        componentEditorGroupBox = QGroupBox("Component Editor")
        componentEditorGridLayout = QGridLayout()
        componentEditorGroupBox.setLayout(componentEditorGridLayout)
        hometopHLayout.addWidget(componentEditorGroupBox)

        tableGroupBox = QGroupBox("Table View")
        homeVLayout.addSpacing(20)
        homeVLayout.addWidget(tableGroupBox)

        tableGroupBoxVLayout = QVBoxLayout()
        tableGroupBox.setLayout(tableGroupBoxVLayout)

        tableWidget = QTableWidget()
        tableWidget.setCornerButtonEnabled(False)
        tableWidget.setAlternatingRowColors(True)
        tableGroupBoxVLayout.addWidget(tableWidget)

        tableLabel = QLabel("DB Table:")
        componentEditorGridLayout.addWidget(tableLabel, 0, 0)
        tableNameCombobox = QComboBox()
        tableNameCombobox.currentTextChanged.connect(loadGUI)
        componentEditorGridLayout.addWidget(tableNameCombobox, 0, 1)

        loadDbLogins()
        testDbConnection()

        ceAddButton = QPushButton("Add new entry")
        ceAddButton.released.connect(addToDatabaseClicked)
        ceAddButton.setEnabled(False)
        ceAddButton.setObjectName("AccentButton")
        ceAddButton.setStyleSheet("QPushButton#AccentButton { background-color: 51b7eb;}")
        componentEditorGridLayout.addWidget(ceAddButton, 7, 4, 1, 2)

        ceNameLabel = QLabel("Name:")
        componentEditorGridLayout.addWidget(ceNameLabel, 1, 0)
        ceNameLineEdit = QLineEdit()
        ceNameLineEdit.textChanged.connect(validateName)
        componentEditorGridLayout.addWidget(ceNameLineEdit, 1, 1)

        ceSupplierLabel = QLabel("Supplier 1:")
        componentEditorGridLayout.addWidget(ceSupplierLabel, 1, 3)
        ceSupplierCombobox = QComboBox()
        ceSupplierCombobox.addItem("Digi-Key")
        ceSupplierCombobox.setCurrentIndex(0)
        componentEditorGridLayout.addWidget(ceSupplierCombobox, 1, 4, 1, 2)

        ceSupplierPnLabel = QLabel("Supplier Part Number 1:")
        componentEditorGridLayout.addWidget(ceSupplierPnLabel, 2, 3)
        ceSupplierPnLineEdit = QLineEdit()
        ceSupplierPnLineEdit.returnPressed.connect(query_supplier)
        componentEditorGridLayout.addWidget(ceSupplierPnLineEdit, 2, 4)

        ceSupplierPnButton = QPushButton()
        ceSupplierPnButton.setIcon(downloadIcon)
        ceSupplierPnButton.setIconSize(QSize(48, 30))
        ceSupplierPnButton.released.connect(query_supplier)
        componentEditorGridLayout.addWidget(ceSupplierPnButton, 2, 5)

        ceLibraryPathLabel = QLabel("Library Path" + ":")
        componentEditorGridLayout.addWidget(ceLibraryPathLabel, 3, 3)
        ceLibraryPathCombobox = QComboBox()
        ceLibraryPathCombobox.currentTextChanged.connect(updateLibraryRefCombobox)
        componentEditorGridLayout.addWidget(ceLibraryPathCombobox, 3, 4, 1, 2)

        ceLibraryRefLabel = QLabel("Library Ref" + ":")
        componentEditorGridLayout.addWidget(ceLibraryRefLabel, 4, 3)
        ceLibraryRefCombobox = QComboBox()
        componentEditorGridLayout.addWidget(ceLibraryRefCombobox, 4, 4, 1, 2)

        ceFootprintPathLabel = QLabel("Footprint Path" + ":")
        componentEditorGridLayout.addWidget(ceFootprintPathLabel, 5, 3)
        ceFootprintPathCombobox = QComboBox()
        ceFootprintPathCombobox.currentTextChanged.connect(updateFootprintRefCombobox)
        componentEditorGridLayout.addWidget(ceFootprintPathCombobox, 5, 4, 1, 2)

        ceFootprintRefLabel = QLabel("Footprint Ref" + ":")
        componentEditorGridLayout.addWidget(ceFootprintRefLabel, 6, 3)
        ceFootprintRefCombobox = QComboBox()
        componentEditorGridLayout.addWidget(ceFootprintRefCombobox, 6, 4, 1, 2)

        componentEditorGridLayout.setSpacing(20)

        getLibSearchPath()

        mainWindow.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    App()