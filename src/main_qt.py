from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, \
    QGroupBox, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget, QFileDialog, QDialog
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QFile, QTextStream, QSize, QThread, QThreadPool
from PyQt5.QtGui import QFont, QFontMetrics, QFontDatabase
import sys
import glob
# noinspection PyUnresolvedReferences
import build.resources
import utils
from json_appdata import *
import mysql_query
from mysql_query import MySqlEditQueryData
import mysql.connector.errors as mysql_errors
import altium_parser
from dk_api import fetchDigikeyData, fetchDigikeySupplierPN
from mouser_api import fetchMouserSupplierPN, MouserSupplierPnExecutor
from parameter_mapping import ParameterMappingGroupBox

permanentParams = ["Name", "Supplier 1", "Supplier Part Number 1", "Library Path",
                   "Library Ref", "Footprint Path", "Footprint Ref"]

mysql_login_filename = 'mysql_server_login.json'
lib_search_path_filename = 'lib_search_path.json'

labels = {}
fields = {}
pendingEditList = []


class App:
    def __init__(self):
        app = QApplication(sys.argv)

        # set stylesheet
        file = QFile(":/style/dark/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())

        appIcon = utils.loadQIcon(':/ui/app.ico')
        homeIcon = utils.loadQIcon(':/ui/home.png')
        settingsIcon = utils.loadQIcon(':/ui/settings.png')
        downloadIcon = utils.loadQIcon(':/ui/download_cloud.png')
        applyIcon = utils.loadQIcon(':/ui/submit.png')
        editIcon = utils.loadQIcon(':/ui/copy.png')
        deleteIcon = utils.loadQIcon(':/ui/delete.png')

        app.setApplicationDisplayName("Altium DB GUI")
        app.setWindowIcon(appIcon)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont('../assets/font/Roboto-Regular.ttf')
        if fontId < 0:
            print("Font not loaded")
        else:
            families = fontDb.applicationFontFamilies(fontId)
            self.fontfamily = families[0]
            print(f"Set application font: {self.fontfamily}")
            app.setFont(QFont(self.fontfamily, 10))

        createFolderIfNotExists(os.getenv('APPDATA') + '\\Altium DB GUI\\')

        self.connected = False
        self.cnx = None

        self.loginInfoDict = {}
        self.dbTableList = []
        self.dbColumnNames = []
        self.cachedTableData = [[]]
        self.dbParamsGroupBox = None
        self.loginInfoDict = {}
        self.availableSuppliers = ['Digi-Key', 'Mouser']

        self.threadPool = QThreadPool.globalInstance()

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.mainWindow = QWidget()
        self.mainWindow.setProperty('mainWindow', True)
        self.mainWindow.setMinimumSize(1920, 1080)
        self.mainWindow.resize(1920, 1440)
        self.mainWindow.setLayout(self.mainLayout)

        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.West)
        self.mainLayout.addWidget(self.tabWidget)

        self.homeWidget = QWidget()
        self.settingsWidget = QWidget()

        self.tabWidget.addTab(self.homeWidget, '')
        self.tabWidget.setTabIcon(0, homeIcon)
        self.tabWidget.addTab(self.settingsWidget, '')
        self.tabWidget.setTabIcon(1, settingsIcon)
        self.tabWidget.setIconSize(QtCore.QSize(64, 64))

        # Settings page widgets
        self.settingsVLayout = QVBoxLayout()
        self.settingsTopHLayout = QHBoxLayout()
        self.settingsWidget.setLayout(self.settingsVLayout)
        self.settingsVLayout.addLayout(self.settingsTopHLayout)
        self.settingsVLayout.addStretch(1)

        self.loginGroupBox = QGroupBox("MySQL Server Login")

        self.settingsTopLeftVLayout = QVBoxLayout()
        self.settingsTopHLayout.addLayout(self.settingsTopLeftVLayout)
        self.settingsTopLeftVLayout.addWidget(self.loginGroupBox, 0)
        self.settingsTopLeftVLayout.addStretch(1)

        self.loginGridLayout = QGridLayout()
        self.loginGroupBox.setLayout(self.loginGridLayout)
        self.loginGridLayout.setColumnMinimumWidth(0, 120)
        self.loginGridLayout.setColumnMinimumWidth(1, 120)
        self.loginGridLayout.setSpacing(20)

        self.dbAddressLabel = QLabel("Address:")
        self.dbAddressLineEdit = QLineEdit()
        self.dbAddressLineEdit.textChanged.connect(lambda s: utils.assignToDict(self.loginInfoDict, 'address', s))
        self.dbAddressLineEdit.textEdited.connect(lambda: self.dbLoginSaveButton.setEnabled(True))
        self.loginGridLayout.addWidget(self.dbAddressLabel, 0, 0)
        self.loginGridLayout.addWidget(self.dbAddressLineEdit, 0, 2)

        self.dbUserLabel = QLabel("User:")
        self.dbUserLineEdit = QLineEdit()
        self.dbUserLineEdit.textChanged.connect(lambda s: utils.assignToDict(self.loginInfoDict, 'user', s))
        self.dbUserLineEdit.textEdited.connect(lambda: self.dbLoginSaveButton.setEnabled(True))
        self.loginGridLayout.addWidget(self.dbUserLabel, 1, 0)
        self.loginGridLayout.addWidget(self.dbUserLineEdit, 1, 2)

        self.dbPasswordLabel = QLabel("Password:")
        self.dbPasswordLineEdit = QLineEdit()
        self.dbPasswordLineEdit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.dbPasswordLineEdit.textChanged.connect(lambda s: utils.assignToDict(self.loginInfoDict, 'password', s))
        self.dbPasswordLineEdit.textEdited.connect(lambda: self.dbLoginSaveButton.setEnabled(True))
        self.loginGridLayout.addWidget(self.dbPasswordLabel, 2, 0)
        self.loginGridLayout.addWidget(self.dbPasswordLineEdit, 2, 2)

        self.dbNameLabel = QLabel("Database:")
        self.dbNameLineEdit = QLineEdit()
        self.dbNameLineEdit.textChanged.connect(lambda s: utils.assignToDict(self.loginInfoDict, 'database', s))
        self.dbNameLineEdit.textEdited.connect(lambda: self.dbLoginSaveButton.setEnabled(True))
        self.loginGridLayout.addWidget(self.dbNameLabel, 3, 0)
        self.loginGridLayout.addWidget(self.dbNameLineEdit, 3, 2)

        self.dbTestButton = QPushButton("Test")
        self.loginGridLayout.addWidget(self.dbTestButton, 4, 0, 1, 2)
        self.dbTestButton.released.connect(self.testDbConnection)

        self.dbLoginSaveButton = QPushButton("Save")
        self.dbLoginSaveButton.setEnabled(False)
        self.dbLoginSaveButton.setProperty('accent', True)
        self.loginGridLayout.addWidget(self.dbLoginSaveButton, 4, 2)
        self.dbLoginSaveButton.released.connect(self.saveDbLogins)

        self.settingsTopRightVLayout = QVBoxLayout()
        self.searchPathHLayout = QHBoxLayout()
        self.settingsTopHLayout.addLayout(self.settingsTopRightVLayout, 1)
        self.settingsTopRightVLayout.addLayout(self.searchPathHLayout)

        self.searchPathLabel = QLabel("Library Search Path:")
        self.searchPathHLayout.addWidget(self.searchPathLabel, 0, Qt.AlignLeft)
        self.searchPathLineEdit = QLineEdit()
        self.searchPathHLayout.addWidget(self.searchPathLineEdit, 1)
        self.searchPathButton = QPushButton("Browse")
        self.searchPathButton.released.connect(self.browseBtn)
        self.searchPathHLayout.addWidget(self.searchPathButton)

        self.settingsTopRightVLayout.addStretch(1)

        # Home page widgets
        self.label1Column = 0
        self.lineEdit1Column = 1
        self.spacingColumn = 3
        self.label2Column = 4
        self.lineEdit2Column = 5
        self.lineEditColSpan = 2

        self.homeVLayout = QVBoxLayout()
        self.homeWidget.setLayout(self.homeVLayout)

        self.hometopHLayout = QHBoxLayout()
        self.homeVLayout.addLayout(self.hometopHLayout)

        self.componentEditorGroupBox = QGroupBox("Component Editor")
        self.ceGridLayout = QGridLayout()
        self.componentEditorGroupBox.setLayout(self.ceGridLayout)
        self.hometopHLayout.addWidget(self.componentEditorGroupBox)

        self.tableGroupBox = QGroupBox("Table View")
        self.homeVLayout.addSpacing(20)
        self.homeVLayout.addWidget(self.tableGroupBox)

        self.tableGroupBoxVLayout = QVBoxLayout()
        self.tableGroupBox.setLayout(self.tableGroupBoxVLayout)

        self.actionsHLayout = QHBoxLayout()
        self.tableGroupBoxVLayout.addLayout(self.actionsHLayout)

        self.tableSearchLineEdit = QLineEdit()
        self.tableSearchLineEdit.setPlaceholderText("Search")
        self.tableSearchLineEdit.setMinimumWidth(500)
        self.tableSearchLineEdit.textChanged.connect(self.filterTable)
        self.actionsHLayout.addWidget(self.tableSearchLineEdit)
        self.actionsHLayout.addStretch(1)

        self.applyChangesButton = QPushButton()
        self.applyChangesButton.setIcon(applyIcon)
        self.applyChangesButton.setIconSize(QSize(40, 40))
        self.applyChangesButton.setDisabled(True)
        self.applyChangesButton.released.connect(self.applyDbEdits)
        self.applyChangesButton.setToolTip("Apply changes")
        self.actionsHLayout.addWidget(self.applyChangesButton)

        self.duplicateButton = QPushButton()
        self.duplicateButton.setIcon(editIcon)
        self.duplicateButton.setIconSize(QSize(40, 40))
        self.duplicateButton.setDisabled(True)
        self.duplicateButton.setToolTip("Duplicate selected row")
        self.actionsHLayout.addWidget(self.duplicateButton)

        self.deleteButton = QPushButton()
        self.deleteButton.setIcon(deleteIcon)
        self.deleteButton.setIconSize(QSize(40, 40))
        self.deleteButton.setDisabled(True)
        self.deleteButton.setToolTip("Delete selected row")
        self.actionsHLayout.addWidget(self.deleteButton)

        self.tableWidget = QTableWidget()
        self.tableWidget.setCornerButtonEnabled(False)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setFont(QFont('Roboto', 9))
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.cellChanged.connect(self.recordDbEdit)
        self.tableWidget.verticalHeader().sectionClicked.connect(self.tableRowClicked)
        self.tableGroupBoxVLayout.addWidget(self.tableWidget)

        self.tableLabel = QLabel("Database Table:")
        self.ceGridLayout.addWidget(self.tableLabel, 0, self.label1Column)
        self.tableNameCombobox = QComboBox()
        self.tableNameCombobox.currentTextChanged.connect(self.loadGUI)
        self.ceGridLayout.addWidget(self.tableNameCombobox, 0, self.lineEdit1Column, 1,
                                    self.lineEditColSpan)

        self.ceAddButton = QPushButton("Add component")
        self.ceAddButton.released.connect(self.addToDatabaseClicked)
        self.ceAddButton.setEnabled(False)
        self.ceAddButton.setProperty("accent", True)
        self.ceAddButton.setStyleSheet("QPushButton#AccentButton { background-color: 51b7eb;}")
        self.ceGridLayout.addWidget(self.ceAddButton, 0, self.lineEdit2Column, 1, self.lineEditColSpan)

        self.ceNameLabel = QLabel("Name:")
        self.ceGridLayout.addWidget(self.ceNameLabel, 1, self.label1Column)
        self.ceNameLineEdit = QLineEdit()
        self.ceNameLineEdit.textChanged.connect(self.validateName)
        fields['name'] = self.ceNameLineEdit
        self.ceGridLayout.addWidget(self.ceNameLineEdit, 1, self.lineEdit1Column, 1, self.lineEditColSpan)

        self.ceSupplier1Label = QLabel("Supplier 1:")
        self.ceGridLayout.addWidget(self.ceSupplier1Label, 1, self.label2Column)
        self.ceSupplier1Combobox = QComboBox()
        self.ceSupplier1Combobox.addItem("Digi-Key")
        self.ceSupplier1Combobox.setCurrentIndex(0)
        fields['supplier 1'] = self.ceSupplier1Combobox
        self.ceGridLayout.addWidget(self.ceSupplier1Combobox, 1, self.lineEdit2Column, 1, self.lineEditColSpan)

        self.ceSupplierPn1Label = QLabel("Supplier Part Number 1:")
        self.ceGridLayout.addWidget(self.ceSupplierPn1Label, 2, self.label2Column)
        self.ceSupplierPn1LineEdit = QLineEdit()
        self.ceSupplierPn1LineEdit.returnPressed.connect(self.querySupplier)
        self.ceSupplierPn1LineEdit.textChanged.connect(
            lambda: utils.setLineEditValidationState(self.ceSupplierPn1LineEdit, None))
        fields['supplier part number 1'] = self.ceSupplierPn1LineEdit
        self.ceGridLayout.addWidget(self.ceSupplierPn1LineEdit, 2, self.lineEdit2Column)

        self.ceSupplierPnButton = QPushButton()
        self.ceSupplierPnButton.setIcon(downloadIcon)
        self.ceSupplierPnButton.setIconSize(QSize(48, 30))
        self.ceSupplierPnButton.setToolTip("Query supplier for part number")
        self.ceSupplierPnButton.released.connect(self.querySupplier)
        self.ceGridLayout.addWidget(self.ceSupplierPnButton, 2, self.lineEdit2Column + 1)

        self.ceSupplier2Label = QLabel("Supplier 2:")
        self.ceGridLayout.addWidget(self.ceSupplier2Label, 3, self.label2Column)
        self.ceSupplier2Combobox = QComboBox()
        self.ceSupplier2Combobox.addItems(utils.strippedList(self.availableSuppliers,
                                          [self.ceSupplier1Combobox.currentText()]))
        self.ceSupplier2Combobox.setCurrentIndex(0)
        fields['supplier 2'] = self.ceSupplier2Combobox
        self.ceGridLayout.addWidget(self.ceSupplier2Combobox, 3, self.lineEdit2Column, 1, self.lineEditColSpan)

        self.ceSupplierPn2Label = QLabel("Supplier Part Number 2:")
        self.ceGridLayout.addWidget(self.ceSupplierPn2Label, 4, self.label2Column)
        self.ceSupplierPn2LineEdit = QLineEdit()
        fields['supplier part number 2'] = self.ceSupplierPn2LineEdit
        self.ceGridLayout.addWidget(self.ceSupplierPn2LineEdit, 4, self.lineEdit2Column, 1, self.lineEditColSpan)

        self.ceLibraryPathLabel = QLabel("Library Path" + ":")
        self.ceGridLayout.addWidget(self.ceLibraryPathLabel, 5, self.label2Column)
        self.ceLibraryPathCombobox = QComboBox()
        self.ceLibraryPathCombobox.currentTextChanged.connect(self.updateLibraryRefCombobox)
        fields['library path'] = self.ceLibraryPathCombobox
        self.ceGridLayout.addWidget(self.ceLibraryPathCombobox, 5, self.lineEdit2Column, 1,
                                    self.lineEditColSpan)

        self.ceLibraryRefLabel = QLabel("Library Ref" + ":")
        self.ceGridLayout.addWidget(self.ceLibraryRefLabel, 6, self.label2Column)
        self.ceLibraryRefCombobox = QComboBox()
        fields['library ref'] = self.ceLibraryRefCombobox
        self.ceGridLayout.addWidget(self.ceLibraryRefCombobox, 6, self.lineEdit2Column, 1,
                                    self.lineEditColSpan)

        self.ceFootprintPathLabel = QLabel("Footprint Path" + ":")
        self.ceGridLayout.addWidget(self.ceFootprintPathLabel, 7, self.label2Column)
        self.ceFootprintPathCombobox = QComboBox()
        self.ceFootprintPathCombobox.currentTextChanged.connect(self.updateFootprintRefCombobox)
        fields['footprint path'] = self.ceFootprintPathCombobox
        self.ceGridLayout.addWidget(self.ceFootprintPathCombobox, 7, self.lineEdit2Column, 1,
                                    self.lineEditColSpan)

        self.ceFootprintRefLabel = QLabel("Footprint Ref" + ":")
        self.ceGridLayout.addWidget(self.ceFootprintRefLabel, 8, self.label2Column)
        self.ceFootprintRefCombobox = QComboBox()
        fields['footprint ref'] = self.ceFootprintRefCombobox
        self.ceGridLayout.addWidget(self.ceFootprintRefCombobox, 8, self.lineEdit2Column, 1,
                                    self.lineEditColSpan)

        self.ceGridLayout.setSpacing(20)
        self.ceGridLayout.setColumnMinimumWidth(self.spacingColumn, 50)
        self.ceGridLayout.setColumnStretch(self.lineEdit1Column, 1)
        self.ceGridLayout.setColumnStretch(self.lineEdit2Column, 1)
        self.ceGridLayout.setColumnMinimumWidth(self.lineEdit2Column + 1, 80)
        self.ceGridLayout.setColumnMinimumWidth(self.lineEdit1Column + 1, 80)

        self.loadDbLogins()
        self.testDbConnection()
        self.loadLibSearchPath()

        self.mainWindow.show()
        self.applyChangesButton.setMinimumWidth(self.ceSupplierPnButton.width())
        self.duplicateButton.setMinimumWidth(self.ceSupplierPnButton.width())
        self.deleteButton.setMinimumWidth(self.ceSupplierPnButton.width())
        self.tableSearchLineEdit.setFixedWidth(max(self.tableWidget.verticalHeader().width() +
                                                   self.tableWidget.columnWidth(0), 400))
        sys.exit(app.exec())

    def loadGUI(self, componentName):
        self.updateCreateComponentFrame()
        self.updateTableViewFrame()
        print(f"Loaded GUI for {componentName}")

    def updateCreateComponentFrame(self):
        row = 2
        for column in self.dbColumnNames:
            if column not in permanentParams:
                # Delete any previously created widgets
                nameLower = column.lower()
                if nameLower in labels:
                    labels[nameLower].deleteLater()
                    del labels[nameLower]
                if nameLower in fields:
                    fields[nameLower].deleteLater()
                    del fields[nameLower]
        self.dbColumnNames.clear()
        self.dbColumnNames = mysql_query.getTableColumns(self.cnx, self.tableNameCombobox.currentText())

        # Create widgets
        for column in self.dbColumnNames:
            if column not in permanentParams:
                nameLower = column.lower()

                label = QLabel(column + ":")
                labels[nameLower] = label
                lineEdit = QLineEdit()
                fields[nameLower] = lineEdit
                self.ceGridLayout.addWidget(label, row, self.label1Column)
                self.ceGridLayout.addWidget(lineEdit, row, self.lineEdit1Column, 1, self.lineEditColSpan)
                row += 1
        self.ceSupplierPn1LineEdit.clear()
        self.ceSupplierPn2LineEdit.clear()
        self.ceNameLineEdit.clear()

    def updateTableViewFrame(self):
        self.cachedTableData = mysql_query.getTableData(self.cnx, self.tableNameCombobox.currentText())

        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(len(self.dbColumnNames))
        self.tableWidget.setRowCount(len(self.cachedTableData))
        self.tableWidget.setHorizontalHeaderLabels(self.dbColumnNames)

        fm = QFontMetrics(QFont(self.fontfamily, 9))
        maxColumnWidth = 500
        widthPadding = 40
        cellWidths = []

        # Insert data
        self.tableWidget.blockSignals(True)
        for row, rowData in enumerate(self.cachedTableData):
            rowWidths = []
            for column, cellData in enumerate(rowData):
                item = QTableWidgetItem(str(cellData))
                self.tableWidget.setItem(row, column, item)
                rowWidths.append(fm.boundingRect(str(cellData)).width() + widthPadding)
            cellWidths.append(rowWidths)
        self.tableWidget.blockSignals(False)
        self.tableWidget.setSortingEnabled(True)

        # Set column widths based on either header, data or maximum allowed width
        for i in range(len(self.dbColumnNames)):
            headerWidth = fm.boundingRect(self.dbColumnNames[i]).width() + widthPadding
            dataWidth = utils.columnMax(cellWidths, i)
            self.tableWidget.setColumnWidth(i, max([min(headerWidth, maxColumnWidth), min(dataWidth, maxColumnWidth)]))

    def querySupplier(self):
        dkpn = self.ceSupplierPn1LineEdit.text()
        print(f"Querying {self.ceSupplier1Combobox.currentText()} for {dkpn}")
        result = fetchDigikeyData(dkpn, utils.strippedList(self.dbColumnNames, permanentParams),
                                  self.dbParamsGroupBox.getParamsDict()[self.tableNameCombobox.currentText()])
        print(result)
        if len(result) == 0:
            utils.setLineEditValidationState(self.ceSupplierPn1LineEdit, False)
        else:
            utils.setLineEditValidationState(self.ceSupplierPn1LineEdit, True)
        for columnName, value in result:
            try:
                fields[columnName.lower()].setText(value)
                fields[columnName.lower()].setCursorPosition(0)
            except KeyError:
                print(f"Error: no field found for \'{columnName.lower()}\'")
        self.queryAlternateSupplier()

    def queryAlternateSupplier(self):
        mfgPN = fields['manufacturer part number'].text()
        alternateSupplierPN = ""
        if len(mfgPN) > 0:
            supplier2 = self.ceSupplier2Combobox.currentText()
            print(f"Querying {supplier2} for {mfgPN}")
            if supplier2 == "Mouser":
                executor = MouserSupplierPnExecutor(mfgPN)
                executor.signals.resultAvailable.connect(lambda s: self.ceSupplierPn2LineEdit.setText(s))
                self.threadPool.start(executor)
            elif supplier2 == "Digi-Key":
                alternateSupplierPN = fetchDigikeySupplierPN(mfgPN)
                print(f"Digi-Key Part Number: {alternateSupplierPN}")
            self.ceSupplierPn2LineEdit.setText(alternateSupplierPN)

    def addToDatabaseClicked(self):
        rowData = []
        for col in self.dbColumnNames:
            try:
                rowData.append(utils.getFieldText(fields[col.lower()]))
            except KeyError:
                print(f"Error: No field found for \'{col.lower()}\'")
                return
        mysql_query.insertInDatabase(self.cnx, self.tableNameCombobox.currentText(), self.dbColumnNames, rowData)
        self.updateTableViewFrame()
        self.updateCreateComponentFrame()

    def validateName(self, name):
        tableWidgetItems = self.tableWidget.findItems(name, Qt.MatchExactly)
        nameExists = False
        for item in tableWidgetItems:
            if item.column() == 0:
                nameExists = True
        if nameExists:
            utils.setLineEditValidationState(self.ceNameLineEdit, False)
        else:
            utils.setLineEditValidationState(self.ceNameLineEdit, None)
        self.ceAddButton.setDisabled(len(name) == 0 or nameExists)

    def loadDbTables(self):
        self.dbTableList = mysql_query.getDatabaseTables(self.cnx)
        self.tableNameCombobox.addItems(self.dbTableList)

    def loadDbLogins(self):
        self.loginInfoDict = loadFromJson(mysql_login_filename)
        if 'address' in self.loginInfoDict:
            self.dbAddressLineEdit.insert(self.loginInfoDict['address'])
        if 'user' in self.loginInfoDict:
            self.dbUserLineEdit.insert(self.loginInfoDict['user'])
        if 'password' in self.loginInfoDict:
            self.dbPasswordLineEdit.insert(self.loginInfoDict['password'])
        if 'database' in self.loginInfoDict:
            self.dbNameLineEdit.insert(self.loginInfoDict['database'])
        self.dbLoginSaveButton.setEnabled(False)

    def saveDbLogins(self):
        saveToJson(mysql_login_filename, self.loginInfoDict)
        self.dbLoginSaveButton.setEnabled(False)

    def testDbConnection(self):
        if not self.connected and len(self.loginInfoDict) > 0 and not utils.dictHasEmptyValue(self.loginInfoDict):
            try:
                self.cnx = mysql_query.init(self.dbUserLineEdit.text(),
                                            self.dbPasswordLineEdit.text(),
                                            self.dbAddressLineEdit.text(),
                                            self.dbNameLineEdit.text())
                if self.cnx.is_connected:
                    self.connected = True
                    print("Connected to database successfully")
                    self.loadDbTables()
                    self.createParameterMappingUI()
                    self.dbTestButton.setDisabled(True)
                    self.dbTestButton.setText("Connected")
                    self.tabWidget.setTabEnabled(0, True)
            except mysql_errors.ProgrammingError:
                print("Access Denied")
            except mysql_errors.InterfaceError:
                print("Invalid Login Information Format")
        if not self.connected:
            self.tabWidget.setTabEnabled(0, False)

    def browseBtn(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dirDict = {}
        if dialog.exec_() == QDialog.Accepted:
            dirDict['filepath'] = dialog.selectedFiles()[0]
            self.updateSearchPath(dirDict['filepath'])
            saveToJson(lib_search_path_filename, dirDict)

    def loadLibSearchPath(self):
        searchPathDict = loadFromJson(lib_search_path_filename)
        if 'filepath' in searchPathDict:
            self.updateSearchPath(searchPathDict['filepath'])

    def updateSearchPath(self, filepath):
        self.searchPathLineEdit.setText(filepath)
        print(f"Library search path set: {filepath}")
        self.updatePathComboboxes(filepath)

    def updatePathComboboxes(self, dirPath):
        schLibFiles = glob.glob(dirPath + '/**/*.SchLib', recursive=True)
        pcbLibFiles = glob.glob(dirPath + '/**/*.PcbLib', recursive=True)
        self.ceLibraryPathCombobox.clear()
        self.ceFootprintPathCombobox.clear()
        for f in schLibFiles:
            self.ceLibraryPathCombobox.addItem(f[f.find('Symbols'):].replace('\\', '/', 255))
        for f in pcbLibFiles:
            self.ceFootprintPathCombobox.addItem(f[f.find('Footprints'):].replace('\\', '/', 255))

    def updateLibraryRefCombobox(self):
        self.ceLibraryRefCombobox.clear()
        self.ceLibraryRefCombobox.addItems(altium_parser.getLibraryRefList(
            self.searchPathLineEdit.text() + '/' + self.ceLibraryPathCombobox.currentText()))

    def updateFootprintRefCombobox(self):
        self.ceFootprintRefCombobox.clear()
        self.ceFootprintRefCombobox.addItems(altium_parser.getFootprintRefList(
            self.searchPathLineEdit.text() + '/' + self.ceFootprintPathCombobox.currentText()))

    def recordDbEdit(self, row, column):
        primaryKey = 'Name'  # TODO: make adaptable
        columnName = self.tableWidget.horizontalHeaderItem(column).text()
        editedValue = self.tableWidget.item(row, column).text()
        pk = None
        pkValue = None
        for i in range(self.tableWidget.columnCount()):
            headerText = self.tableWidget.horizontalHeaderItem(i).text()
            if headerText == primaryKey:
                pk = headerText
                pkValue = str(self.cachedTableData[row][i])
        if pk is not None:
            self.applyChangesButton.setEnabled(True)
            for edit in pendingEditList:
                if pkValue == edit.pkValue:
                    edit.append(columnName, editedValue)
                    return
            queryData = MySqlEditQueryData(columnName, editedValue, pk, pkValue)
            pendingEditList.append(queryData)
        else:
            print("Error while finding edit's corresponding primary key")

    def applyDbEdits(self):
        mysql_query.editDatabase(self.cnx, self.loginInfoDict['database'],
                                 self.tableNameCombobox.currentText(), pendingEditList)
        self.applyChangesButton.setEnabled(False)
        pendingEditList.clear()
        self.updateTableViewFrame()

    def filterTable(self, searchStr):
        matches = self.tableWidget.findItems(searchStr, Qt.MatchContains)
        rows = list(range(self.tableWidget.rowCount()))
        for item in matches:
            try:
                self.tableWidget.setRowHidden(item.row(), False)
                rows.remove(item.row())
            except ValueError:
                pass
        for r in rows:
            self.tableWidget.setRowHidden(r, True)

    def tableRowClicked(self, row):
        print(f"Row {row} selected")
        self.duplicateButton.setEnabled(True)
        self.deleteButton.setEnabled(True)

    def createParameterMappingUI(self):
        tablesColumns = []
        for table in self.dbTableList:
            unfilteredColumns = mysql_query.getTableColumns(self.cnx, table)
            filteredColumns = []
            for col in unfilteredColumns:
                if col not in permanentParams and \
                        col not in ['Description', 'Manufacturer', 'Manufacturer Part Number']:
                    filteredColumns.append(col)
            tablesColumns.append(filteredColumns)
        self.dbParamsGroupBox = ParameterMappingGroupBox(self.dbTableList, tablesColumns, ['Digi-Key'])
        self.settingsTopRightVLayout.takeAt(1)
        self.settingsTopRightVLayout.addWidget(self.dbParamsGroupBox)
        self.settingsTopRightVLayout.addStretch(1)


if __name__ == "__main__":
    App()
