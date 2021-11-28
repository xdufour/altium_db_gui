from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,\
    QGroupBox, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget, QFileDialog, QDialog
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QFile, QTextStream, QSize
from PyQt5.QtGui import QFont, QFontMetrics, QFontDatabase
import sys
import glob
import breeze_resources
import utils
import json_appdata
import mysql_query
from mysql_query import MySqlEditQueryData
import mysql
import altium_parser
import dk_api

permanentParams = ["Name", "Supplier 1", "Supplier Part Number 1", "Library Path",
                   "Library Ref", "Footprint Path", "Footprint Ref"]

labels = {}
fields = {}
pendingEditList = []


def getDbTableList(mysql_cnx):
    dbTableList = []
    dbTableCursor = mysql_query.getDatabaseTables(mysql_cnx)
    for it in dbTableCursor:
        dbTableList.append(it[0])
    return dbTableList


def setLineEditValidationState(lineEdit, state):
    lineEdit.setProperty('valid', state)
    lineEdit.style().unpolish(lineEdit)
    lineEdit.style().unpolish(lineEdit)
    lineEdit.repaint()


class App:
    def __init__(self):
        app = QApplication(sys.argv)

        appIcon = utils.loadQIcon('assets/app.ico')
        homeIcon = utils.loadQIcon('assets/home.png')
        settingsIcon = utils.loadQIcon('assets/settings.png')
        downloadIcon = utils.loadQIcon('assets/download_cloud.png')
        applyIcon = utils.loadQIcon('assets/submit.png')
        editIcon = utils.loadQIcon('assets/copy.png')
        deleteIcon = utils.loadQIcon('assets/delete.png')

        app.setApplicationDisplayName("Altium DB GUI")
        app.setWindowIcon(appIcon)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont('assets/font/Roboto-Regular.ttf')
        if fontId < 0:
            print("Font not loaded")
        else:
            families = fontDb.applicationFontFamilies(fontId)
            self.fontfamily = families[0]
            print(f"Set application font: {self.fontfamily}")
            app.setFont(QFont(self.fontfamily, 10))

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

            self.dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnListCursor):
                self.dbColumnNames.append(column[0])
                if self.dbColumnNames[i] not in permanentParams:
                    # Delete any previously created widgets
                    nameLower = self.dbColumnNames[i].lower()
                    if nameLower in labels:
                        labels[nameLower].deleteLater()
                        del labels[nameLower]
                    if nameLower in fields:
                        fields[nameLower].deleteLater()
                        del fields[nameLower]

                    label = QLabel(self.dbColumnNames[i] + ":")
                    labels[nameLower] = label
                    lineEdit = QLineEdit()
                    fields[nameLower] = lineEdit
                    componentEditorGridLayout.addWidget(label, row, label1Column)
                    componentEditorGridLayout.addWidget(lineEdit, row, lineEdit1Column, 1, lineEditColSpan)
                    row += 1

        def updateTableViewFrame():
            dbDataCursor = mysql_query.getTableData(self.cnx, tableNameCombobox.currentText())
            data = dbDataCursor.fetchall()

            tableWidget.setSortingEnabled(False)
            tableWidget.clear()
            tableWidget.setColumnCount(len(self.dbColumnNames))
            tableWidget.setRowCount(len(data))
            tableWidget.setHorizontalHeaderLabels(self.dbColumnNames)

            fm = QFontMetrics(QFont(self.fontfamily, 9))
            maxColumnWidth = 500
            widthPadding = 40
            cellWidths = []

            # Insert data
            tableWidget.blockSignals(True)
            for row, cellData in enumerate(data):
                rowWidths = []
                for column, cellData in enumerate(cellData):
                    item = QTableWidgetItem(str(cellData))
                    tableWidget.setItem(row, column, item)
                    rowWidths.append(fm.boundingRect(str(cellData)).width() + widthPadding)
                cellWidths.append(rowWidths)
            tableWidget.blockSignals(False)

            # Set column widths based on either header, data or maximum allowed width
            for i in range(len(self.dbColumnNames)):
                headerWidth = fm.boundingRect(self.dbColumnNames[i]).width() + widthPadding
                dataWidth = utils.columnMax(cellWidths, i)
                tableWidget.setColumnWidth(i, max([min(headerWidth, maxColumnWidth), min(dataWidth, maxColumnWidth)]))

            tableWidget.setSortingEnabled(True)

        def querySupplier():
            dkpn = ceSupplierPnLineEdit.text()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, tableNameCombobox.currentText(), utils.strippedList(self.dbColumnNames, permanentParams))
            print(result)
            if len(result) == 0:
                setLineEditValidationState(ceSupplierPnLineEdit, False)
            else:
                setLineEditValidationState(ceSupplierPnLineEdit, True)
            for columnName, value in result:
                try:
                    fields[columnName.lower()].setText(value)
                    fields[columnName.lower()].setCursorPosition(0)
                except KeyError:
                    print(f"Error: no field found for \'{columnName.lower()}\'")

        def addToDatabaseClicked():
            rowData = []
            for col in self.dbColumnNames:
                try:
                    rowData.append(utils.getFieldText(fields[col.lower()]))
                except KeyError:
                    print(f"Error: No field found for \'{col.lower()}\'")
                    return
            mysql_query.insertInDatabase(self.cnx, tableNameCombobox.currentText(), self.dbColumnNames, rowData)
            updateTableViewFrame()

        def validateName(name):
            tableWidgetItems = tableWidget.findItems(name, Qt.MatchExactly)
            nameExists = False
            for item in tableWidgetItems:
                if item.column() == 0:
                    nameExists = True
            ceNameLineEdit.setProperty('valid', not nameExists)
            ceNameLineEdit.style().unpolish(ceNameLineEdit)
            ceNameLineEdit.style().polish(ceNameLineEdit)
            ceAddButton.setDisabled(len(name) == 0 or nameExists)

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

        def recordDbEdit(row, column):
            primaryKey = 'Name'  # TODO: make adaptable
            editedValue = tableWidget.item(row, column).text()
            valueHeader = tableWidget.horizontalHeaderItem(column).text()
            pk = None
            for i in range(tableWidget.columnCount()):
                headerText = tableWidget.horizontalHeaderItem(i).text()
                if headerText == primaryKey:
                    pk = headerText
                    pkValue = tableWidget.item(row, i).text()
            if pk is not None:
                queryData = MySqlEditQueryData(valueHeader, editedValue, pk, pkValue)
                pendingEditList.append(queryData)
                applyChangesButton.setEnabled(True)
            else:
                print("Error while finding edit's corresponding primary key")

        def applyDbEdits():
            print("Apply")

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
        label1Column = 0
        lineEdit1Column = 1
        spacingColumn = 3
        label2Column = 4
        lineEdit2Column = 5
        lineEditColSpan = 2

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

        actionsHLayout = QHBoxLayout()
        tableGroupBoxVLayout.addLayout(actionsHLayout)
        actionsHLayout.addStretch(1)

        applyChangesButton = QPushButton()
        applyChangesButton.setIcon(applyIcon)
        applyChangesButton.setIconSize(QSize(40, 40))
        applyChangesButton.setDisabled(True)
        applyChangesButton.released.connect(applyDbEdits)
        applyChangesButton.setToolTip("Apply changes")
        actionsHLayout.addWidget(applyChangesButton)

        duplicateButton = QPushButton()
        duplicateButton.setIcon(editIcon)
        duplicateButton.setIconSize(QSize(40, 40))
        duplicateButton.setDisabled(True)
        duplicateButton.setToolTip("Duplicate selected row")
        actionsHLayout.addWidget(duplicateButton)

        deleteButton = QPushButton()
        deleteButton.setIcon(deleteIcon)
        deleteButton.setIconSize(QSize(40, 40))
        deleteButton.setDisabled(True)
        deleteButton.setToolTip("Delete selected row")
        actionsHLayout.addWidget(deleteButton)

        tableWidget = QTableWidget()
        tableWidget.setCornerButtonEnabled(False)
        tableWidget.setAlternatingRowColors(True)
        tableWidget.setFont(QFont('Roboto', 9))
        tableWidget.setWordWrap(False)
        tableWidget.cellChanged.connect(recordDbEdit)
        tableGroupBoxVLayout.addWidget(tableWidget)

        tableLabel = QLabel("DB Table:")
        componentEditorGridLayout.addWidget(tableLabel, 0, label1Column)
        tableNameCombobox = QComboBox()
        tableNameCombobox.currentTextChanged.connect(loadGUI)
        componentEditorGridLayout.addWidget(tableNameCombobox, 0, lineEdit1Column, 1, lineEditColSpan)

        loadDbLogins()
        testDbConnection()

        ceAddButton = QPushButton("Add new entry")
        ceAddButton.released.connect(addToDatabaseClicked)
        ceAddButton.setEnabled(False)
        ceAddButton.setProperty("accent", True)
        ceAddButton.setStyleSheet("QPushButton#AccentButton { background-color: 51b7eb;}")
        componentEditorGridLayout.addWidget(ceAddButton, 7, lineEdit2Column, 1, lineEditColSpan)

        ceNameLabel = QLabel("Name:")
        componentEditorGridLayout.addWidget(ceNameLabel, 1, label1Column)
        ceNameLineEdit = QLineEdit()
        ceNameLineEdit.textChanged.connect(validateName)
        fields['name'] = ceNameLineEdit
        componentEditorGridLayout.addWidget(ceNameLineEdit, 1, lineEdit1Column, 1, lineEditColSpan)

        ceSupplierLabel = QLabel("Supplier 1:")
        componentEditorGridLayout.addWidget(ceSupplierLabel, 1, label2Column)
        ceSupplierCombobox = QComboBox()
        ceSupplierCombobox.addItem("Digi-Key")
        ceSupplierCombobox.setCurrentIndex(0)
        fields['supplier 1'] = ceSupplierCombobox
        componentEditorGridLayout.addWidget(ceSupplierCombobox, 1, lineEdit2Column, 1, lineEditColSpan)

        ceSupplierPnLabel = QLabel("Supplier Part Number 1:")
        componentEditorGridLayout.addWidget(ceSupplierPnLabel, 2, label2Column)
        ceSupplierPnLineEdit = QLineEdit()
        ceSupplierPnLineEdit.returnPressed.connect(querySupplier)
        ceSupplierPnLineEdit.textChanged.connect(lambda: setLineEditValidationState(ceSupplierPnLineEdit, None))
        fields['supplier part number 1'] = ceSupplierPnLineEdit
        componentEditorGridLayout.addWidget(ceSupplierPnLineEdit, 2, lineEdit2Column)

        ceSupplierPnButton = QPushButton()
        ceSupplierPnButton.setIcon(downloadIcon)
        ceSupplierPnButton.setIconSize(QSize(48, 30))
        ceSupplierPnButton.setToolTip("Query supplier for part number")
        ceSupplierPnButton.released.connect(querySupplier)
        componentEditorGridLayout.addWidget(ceSupplierPnButton, 2, lineEdit2Column + 1)

        ceLibraryPathLabel = QLabel("Library Path" + ":")
        componentEditorGridLayout.addWidget(ceLibraryPathLabel, 3, label2Column)
        ceLibraryPathCombobox = QComboBox()
        ceLibraryPathCombobox.currentTextChanged.connect(updateLibraryRefCombobox)
        fields['library path'] = ceLibraryPathCombobox
        componentEditorGridLayout.addWidget(ceLibraryPathCombobox, 3, lineEdit2Column, 1, lineEditColSpan)

        ceLibraryRefLabel = QLabel("Library Ref" + ":")
        componentEditorGridLayout.addWidget(ceLibraryRefLabel, 4, label2Column)
        ceLibraryRefCombobox = QComboBox()
        fields['library ref'] = ceLibraryRefCombobox
        componentEditorGridLayout.addWidget(ceLibraryRefCombobox, 4, lineEdit2Column, 1, lineEditColSpan)

        ceFootprintPathLabel = QLabel("Footprint Path" + ":")
        componentEditorGridLayout.addWidget(ceFootprintPathLabel, 5, label2Column)
        ceFootprintPathCombobox = QComboBox()
        ceFootprintPathCombobox.currentTextChanged.connect(updateFootprintRefCombobox)
        fields['footprint path'] = ceFootprintPathCombobox
        componentEditorGridLayout.addWidget(ceFootprintPathCombobox, 5, lineEdit2Column, 1, lineEditColSpan)

        ceFootprintRefLabel = QLabel("Footprint Ref" + ":")
        componentEditorGridLayout.addWidget(ceFootprintRefLabel, 6, label2Column)
        ceFootprintRefCombobox = QComboBox()
        fields['footprint ref'] = ceFootprintRefCombobox
        componentEditorGridLayout.addWidget(ceFootprintRefCombobox, 6, lineEdit2Column, 1, lineEditColSpan)

        componentEditorGridLayout.setSpacing(20)
        componentEditorGridLayout.setColumnMinimumWidth(spacingColumn, 50)
        componentEditorGridLayout.setColumnStretch(lineEdit1Column, 1)
        componentEditorGridLayout.setColumnStretch(lineEdit2Column, 1)
        componentEditorGridLayout.setColumnMinimumWidth(lineEdit2Column + 1, 80)
        componentEditorGridLayout.setColumnMinimumWidth(lineEdit1Column + 1, 80)

        getLibSearchPath()

        mainWindow.show()
        applyChangesButton.setMinimumWidth(ceSupplierPnButton.width())
        duplicateButton.setMinimumWidth(ceSupplierPnButton.width())
        deleteButton.setMinimumWidth(ceSupplierPnButton.width())
        sys.exit(app.exec())


if __name__ == "__main__":
    App()