from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, \
    QGroupBox, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTabWidget, QFileDialog, QDialog, QMessageBox, \
    QScroller, QScrollerProperties
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QFile, QTextStream, QSize, QThreadPool
from PyQt5.QtGui import QFont, QFontMetrics, QFontDatabase
import sys
import glob
# noinspection PyUnresolvedReferences
import resources
import utils
from json_appdata import *
from mysql_query import MySQLQuery, MySqlEditQueryData
import altium_parser
from dk_api import fetchDigikeyData, fetchDigikeySupplierPN
from mouser_api import fetchMouserSupplierPN
from parameter_mapping import ParameterMappingGroupBox
from executor import Executor
from main_window import MainWindow
from statusbar_widget import *

permanentParams = ["Name", "Library Path", "Library Ref", "Footprint Path", "Footprint Ref"]

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
        fontId = fontDb.addApplicationFont(':/font/Roboto-Regular.ttf')
        self.fontSize = 10
        if fontId < 0:
            print("Font not loaded")
        else:
            families = fontDb.applicationFontFamilies(fontId)
            self.fontFamily = families[0]
            print(f"Set application font: {self.fontFamily}, {self.fontSize}pt")
            app.setFont(QFont(self.fontFamily, self.fontSize))

        fm = QFontMetrics(QFont(self.fontFamily, self.fontSize))
        self.textHeight = fm.boundingRect("Text").height()

        createFolderIfNotExists(os.getenv('APPDATA') + '\\Altium DB GUI\\')

        self.connectedToDb = False
        self.mySqlQuery = None

        self.loginInfoDict = {}
        self.dbTableList = []
        self.dbColumnNames = []
        self.supplierParams = []
        self.cachedTableData = [[]]
        self.dbParamsGroupBox = None
        self.loginInfoDict = {}
        self.currentSelectedRowPkValue = ""
        self.availableSuppliers = ['Digi-Key']
        self.availableAlternateSuppliers = ['Digi-Key', 'Mouser']

        self.threadPool = QThreadPool.globalInstance()

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.mainWindow = MainWindow()
        screenSize = QApplication.desktop().screenGeometry()
        aspectRatio = screenSize.width() / screenSize.height()
        self.mainWindow.setMinimumSize(round(screenSize.width() * (1.5 - (0.5 * aspectRatio))),
                                       round(screenSize.height() * 0.8))
        app.installEventFilter(self.mainWindow)
        self.mainWindow.mousePressed.connect(self.windowClicked)

        self.centralWidget = QWidget()
        self.mainWindow.setCentralWidget(self.centralWidget)
        self.centralWidget.setProperty('mainWindow', True)
        self.centralWidget.setLayout(self.mainLayout)

        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.West)
        self.mainLayout.addWidget(self.tabWidget)

        self.statusBar = StatusBar(self.textHeight)
        self.mainLayout.addWidget(self.statusBar)

        self.homeWidget = QWidget()
        self.settingsWidget = QWidget()

        self.tabWidget.addTab(self.homeWidget, '')
        self.tabWidget.setTabIcon(0, homeIcon)
        self.tabWidget.addTab(self.settingsWidget, '')
        self.tabWidget.setTabIcon(1, settingsIcon)
        self.tabWidget.setIconSize(QtCore.QSize(round(self.textHeight * 2.25), round(self.textHeight * 2.25)))

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
        self.loginGridLayout.setColumnMinimumWidth(0, round(self.textHeight * 3.6))
        self.loginGridLayout.setColumnStretch(0, 1)
        self.loginGridLayout.setColumnMinimumWidth(1, round(self.textHeight * 3.6))
        self.loginGridLayout.setColumnStretch(1, 1)
        self.loginGridLayout.setSpacing(round(self.textHeight * 0.6))

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

        self.dbConnectButton = QPushButton("Connect")
        self.loginGridLayout.addWidget(self.dbConnectButton, 4, 0, 1, 2)
        self.dbConnectButton.released.connect(self.testDbConnection)

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
        self.homeVLayout.addSpacing(round(self.textHeight * 0.6))
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

        tableIconSize = round(self.textHeight * 1.4)

        self.applyChangesButton = QPushButton()
        self.applyChangesButton.setIcon(applyIcon)
        self.applyChangesButton.setIconSize(QSize(tableIconSize, tableIconSize))
        self.applyChangesButton.setDisabled(True)
        self.applyChangesButton.released.connect(self.applyDbEdits)
        self.applyChangesButton.setToolTip("Apply changes")
        self.actionsHLayout.addWidget(self.applyChangesButton)

        self.duplicateButton = QPushButton()
        self.duplicateButton.setIcon(editIcon)
        self.duplicateButton.setIconSize(QSize(tableIconSize, tableIconSize))
        self.duplicateButton.setDisabled(True)
        self.duplicateButton.setObjectName("DuplicateButton")
        self.duplicateButton.setToolTip("Duplicate selected row")
        self.duplicateButton.released.connect(self.duplicateDbRow)
        self.actionsHLayout.addWidget(self.duplicateButton)

        self.deleteButton = QPushButton()
        self.deleteButton.setIcon(deleteIcon)
        self.deleteButton.setIconSize(QSize(tableIconSize, tableIconSize))
        self.deleteButton.setDisabled(True)
        self.deleteButton.setToolTip("Delete selected row")
        self.deleteButton.setObjectName("DeleteButton")
        self.deleteButton.released.connect(self.deleteDbRow)
        self.actionsHLayout.addWidget(self.deleteButton)

        self.tableWidget = QTableWidget()
        self.tableWidget.setCornerButtonEnabled(False)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setFont(QFont('Roboto', 9))
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setFocusPolicy(Qt.ClickFocus)
        self.tableWidget.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        scrollerProperties = QScrollerProperties()
        scrollerProperties.setScrollMetric(QScrollerProperties.HorizontalOvershootPolicy,
                                           QScrollerProperties.OvershootAlwaysOff)
        scrollerProperties.setScrollMetric(QScrollerProperties.VerticalOvershootPolicy,
                                           QScrollerProperties.OvershootAlwaysOff)
        scroller = QScroller.scroller(self.tableWidget.viewport())
        scroller.setScrollerProperties(scrollerProperties)
        scroller.grabGesture(self.tableWidget.viewport(), QScroller.TouchGesture)
        self.tableWidget.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.tableWidget.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.tableWidget.cellChanged.connect(self.recordDbEdit)
        self.tableWidget.cellClicked.connect(lambda: self.setTableButtonsEnabled(False))
        self.tableWidget.verticalHeader().sectionClicked.connect(self.tableRowClicked)
        self.tableGroupBoxVLayout.addWidget(self.tableWidget)

        self.tableLabel = QLabel("Database Table:")
        self.ceGridLayout.addWidget(self.tableLabel, 0, self.label1Column)
        self.tableNameCombobox = QComboBox()
        self.tableNameCombobox.currentTextChanged.connect(self.loadGUI)
        self.ceGridLayout.addWidget(self.tableNameCombobox, 0, self.lineEdit1Column, 1, self.lineEditColSpan)

        self.ceAddButton = QPushButton("Add component")
        self.ceAddButton.released.connect(self.addToDatabaseClicked)
        self.ceAddButton.setEnabled(False)
        self.ceAddButton.setProperty("accent", True)
        self.ceGridLayout.addWidget(self.ceAddButton, 0, self.lineEdit2Column, 1, self.lineEditColSpan)

        self.ceNameLabel = QLabel("Name:")
        self.ceGridLayout.addWidget(self.ceNameLabel, 1, self.label1Column)
        self.ceNameLineEdit = QLineEdit()
        self.ceNameLineEdit.textChanged.connect(self.validateName)
        fields['name'] = self.ceNameLineEdit
        self.ceGridLayout.addWidget(self.ceNameLineEdit, 1, self.lineEdit1Column, 1, self.lineEditColSpan)
        self.mainWindow.installEventFilter(self.ceNameLineEdit)

        self.ceSupplier1Label = QLabel("Supplier 1:")
        self.ceGridLayout.addWidget(self.ceSupplier1Label, 1, self.label2Column)
        self.ceSupplier1Combobox = QComboBox()
        self.ceSupplier1Combobox.addItems(self.availableSuppliers)
        self.ceSupplier1Combobox.setCurrentIndex(0)
        self.ceSupplier1Combobox.setEditable(True)
        self.ceSupplier1Combobox.currentTextChanged.connect(self.mainSupplierComboBoxChanged)
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

        self.ceQuerySupplierButton = QPushButton()
        self.ceQuerySupplierButton.setIcon(downloadIcon)
        self.ceQuerySupplierButton.setIconSize(QSize(round(self.textHeight * 1.5), self.textHeight))
        self.ceQuerySupplierButton.setFixedWidth(round(self.textHeight * 2.6))
        self.ceQuerySupplierButton.setToolTip("Query supplier for part number")
        self.ceQuerySupplierButton.released.connect(self.querySupplier)
        self.ceGridLayout.addWidget(self.ceQuerySupplierButton, 2, self.lineEdit2Column + 1, alignment=Qt.AlignRight)

        self.ceSupplier2Label = QLabel("Supplier 2:")
        self.ceGridLayout.addWidget(self.ceSupplier2Label, 3, self.label2Column)
        self.ceSupplier2Combobox = QComboBox()
        self.ceSupplier2Combobox.setEditable(True)
        self.ceSupplier2Combobox.addItems(utils.strippedList(self.availableAlternateSuppliers,
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

        self.ceGridLayout.setSpacing(round(self.textHeight * 0.6))
        self.ceGridLayout.setColumnMinimumWidth(self.spacingColumn, round(self.textHeight * 1.5))
        self.ceGridLayout.setColumnStretch(self.lineEdit1Column, 1)
        self.ceGridLayout.setColumnStretch(self.lineEdit2Column, 1)
        self.ceGridLayout.setColumnMinimumWidth(self.lineEdit2Column + 1, round(self.textHeight * 2.5))
        self.ceGridLayout.setColumnMinimumWidth(self.lineEdit1Column + 1, round(self.textHeight * 2.5))

        self.loadDbLogins()
        self.testDbConnection()
        self.loadLibSearchPath()

        self.mainWindow.show()
        self.statusBar.setOffsetWidth(self.tabWidget.tabBar().width())
        self.applyChangesButton.setMinimumWidth(self.ceQuerySupplierButton.width())
        self.duplicateButton.setMinimumWidth(self.ceQuerySupplierButton.width())
        self.deleteButton.setMinimumWidth(self.ceQuerySupplierButton.width())
        self.tableSearchLineEdit.setFixedWidth(max(self.tableWidget.verticalHeader().width() +
                                                   self.tableWidget.columnWidth(0), self.textHeight * 12))
        sys.exit(app.exec())

    def loadGUI(self, table):
        if not self.isDbConnectionValid():
            return
        self.updateCreateComponentFrame()
        self.updateTableViewFrame()
        print(f"Loaded GUI for {table}")

    def updateCreateComponentFrame(self):
        row = 2
        for column in self.dbColumnNames:
            if column not in permanentParams + self.supplierParams:
                # Delete any previously created widgets
                nameLower = column.lower()
                if nameLower in labels:
                    labels[nameLower].deleteLater()
                    del labels[nameLower]
                if nameLower in fields:
                    fields[nameLower].deleteLater()
                    del fields[nameLower]
        self.dbColumnNames.clear()
        self.dbColumnNames = self.mySqlQuery.getTableColumns(self.tableNameCombobox.currentText())
        self.supplierParams = utils.matchFromList("Supplier\s*(Part Number)?\s*[1-9]", self.dbColumnNames)

        # Create widgets
        for column in self.dbColumnNames:
            if column not in permanentParams + self.supplierParams:
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
        self.cachedTableData = self.mySqlQuery.getTableData(self.tableNameCombobox.currentText())
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(len(self.dbColumnNames))
        self.tableWidget.setRowCount(len(self.cachedTableData))
        self.tableWidget.setHorizontalHeaderLabels(self.dbColumnNames)

        fm = QFontMetrics(QFont(self.fontFamily, 9))
        maxColumnWidth = fm.boundingRect("Text").height() * 18
        widthPadding = round(fm.boundingRect("Text").height() * 1.3)
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
        if not self.ceQuerySupplierButton.isEnabled():
            return
        self.statusBar.setStatus(f"Querying supplier for component attributes...", StatusColor.Default)
        pn = self.ceSupplierPn1LineEdit.text()
        print(f"Querying {self.ceSupplier1Combobox.currentText()} for {pn}")
        result = fetchDigikeyData(pn, utils.strippedList(self.dbColumnNames, permanentParams + self.supplierParams),
                                  self.dbParamsGroupBox.getParamsDict()[self.tableNameCombobox.currentText()])
        print(result)
        if len(result) == 0:
            utils.setLineEditValidationState(self.ceSupplierPn1LineEdit, False)
            self.statusBar.setStatus(f"Supplier API Request Failed",
                                     StatusColor.Red)
        else:
            utils.setLineEditValidationState(self.ceSupplierPn1LineEdit, True)
            self.statusBar.setStatus(f"Supplier API Request Successful",
                                     StatusColor.Green)
        for columnName, value in result:
            try:
                fields[columnName.lower()].setText(value)
                fields[columnName.lower()].setCursorPosition(0)
            except KeyError:
                print(f"Warning: no field found for \'{columnName.lower()}\'")
        self.queryAlternateSupplier()

    def queryAlternateSupplier(self):
        mfgPN = fields['manufacturer part number'].text()
        executor = None
        if len(mfgPN) > 0:
            supplier2 = self.ceSupplier2Combobox.currentText()
            print(f"Querying {supplier2} for {mfgPN}")
            if supplier2 == "Mouser":
                executor = Executor(fetchMouserSupplierPN, mfgPN)
            elif supplier2 == "Digi-Key":
                executor = Executor(fetchDigikeySupplierPN, mfgPN)
            if executor is not None:
                executor.signals.resultAvailable.connect(lambda s: self.ceSupplierPn2LineEdit.setText(s))
                self.threadPool.start(executor)

    def addToDatabaseClicked(self):
        if not self.isDbConnectionValid():
            return
        rowData = []
        for col in self.dbColumnNames:
            rowData.append(utils.getFieldText(fields.get(col.lower(), "")))
        result = self.mySqlQuery.insertInDatabase(self.tableNameCombobox.currentText(), self.dbColumnNames, rowData)
        if result:
            self.statusBar.setStatus('Component inserted into database successfully', StatusColor.Green)
        else:
            self.statusBar.setStatus('Failed to commit new row to database', StatusColor.Red)
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

    def isDbConnectionValid(self):
        if self.mySqlQuery.isConnected():
            return True
        else:
            self.statusBar.setStatus(self.mySqlQuery.errorMsg, StatusColor.Red)
            self.connectedToDb = False

    def loadDbTables(self):
        if not self.isDbConnectionValid():
            return
        self.dbTableList = self.mySqlQuery.getDatabaseTables()
        self.tableNameCombobox.addItems(self.dbTableList)

    def loadDbLogins(self):
        self.loginInfoDict = loadFromJson(mysql_login_filename)
        self.dbAddressLineEdit.insert(self.loginInfoDict.get('address', ''))
        self.dbUserLineEdit.insert(self.loginInfoDict.get('user', ''))
        self.dbPasswordLineEdit.insert(self.loginInfoDict.get('password', ''))
        self.dbNameLineEdit.insert(self.loginInfoDict.get('database', ''))
        self.dbLoginSaveButton.setEnabled(False)

    def saveDbLogins(self):
        saveToJson(mysql_login_filename, self.loginInfoDict)
        self.dbLoginSaveButton.setEnabled(False)

    def testDbConnection(self):
        if not self.connectedToDb and len(self.loginInfoDict) > 0 and not utils.dictHasEmptyValue(self.loginInfoDict):
            self.mySqlQuery = MySQLQuery(self.dbUserLineEdit.text(),
                                         self.dbPasswordLineEdit.text(),
                                         self.dbAddressLineEdit.text(),
                                         self.dbNameLineEdit.text())
            if self.mySqlQuery.isConnected():
                self.connectedToDb = True
                self.loadDbTables()
                self.createParameterMappingUI()
                self.dbConnectButton.setDisabled(True)
                self.dbConnectButton.setText("Connected")
                self.tabWidget.setTabEnabled(0, True)
                print("Connected to database successfully")
                self.statusBar.setStatus(f"Successfully connected to "
                                         f"{self.dbNameLineEdit.text()} at {self.dbAddressLineEdit.text()}",
                                         StatusColor.Green)
            else:
                self.statusBar.setStatus(self.mySqlQuery.errorMsg, StatusColor.Red)
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
        self.updateSearchPath(searchPathDict.get('filepath', ''))

    def updateSearchPath(self, filepath):
        self.searchPathLineEdit.setText(filepath)
        print(f"Library search path set: {filepath}")
        self.updatePathComboboxes(filepath)

    def updatePathComboboxes(self, dirPath):
        if len(dirPath) > 0:
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

    def mainSupplierComboBoxChanged(self, text):
        self.ceQuerySupplierButton.setEnabled(text in self.availableSuppliers)
        self.ceSupplier2Combobox.clear()
        self.ceSupplier2Combobox.addItems(
            utils.strippedList(self.availableAlternateSuppliers, [text]))

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
        self.statusBar.setStatus('Applying changes...', StatusColor.Default)
        if not self.isDbConnectionValid():
            return
        result = self.mySqlQuery.editDatabase(self.tableNameCombobox.currentText(), pendingEditList)
        if result:
            self.statusBar.setStatus('Changes committed to database successfully', StatusColor.Green)
        else:
            self.statusBar.setStatus('Failed to commit one or more changes to database', StatusColor.Red)
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
        self.tableWidget.clearSelection()
        self.tableWidget.selectRow(row)
        self.currentSelectedRowPkValue = self.tableWidget.item(row, 0).text()
        self.setTableButtonsEnabled(True)

    def windowClicked(self, objectName):
        if objectName != 'qt_scrollarea_viewport' and objectName != 'DeleteButton' and objectName != 'DuplicateButton':
            self.setTableButtonsEnabled(False)
            self.tableWidget.clearSelection()

    def setTableButtonsEnabled(self, state):
        self.duplicateButton.setEnabled(state)
        self.deleteButton.setEnabled(state)

    def duplicateDbRow(self):
        if not self.isDbConnectionValid():
            return
        rowData = [item.text() for item in self.tableWidget.selectedItems()]
        rowData[0] += '_1'
        self.setTableButtonsEnabled(False)
        self.mySqlQuery.insertInDatabase(self.tableNameCombobox.currentText(), self.dbColumnNames, rowData)
        self.updateTableViewFrame()

    def deleteDbRow(self):
        msgBox = QMessageBox(QMessageBox.Question, 'Confirm Deletion', f'Permanently delete database entry '
                                                                       f'\'{self.currentSelectedRowPkValue}\'?')
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if msgBox.exec() == QMessageBox.Ok:
            if not self.isDbConnectionValid():
                return
            self.setTableButtonsEnabled(False)
            result = self.mySqlQuery.deleteRowFromDatabase(self.tableNameCombobox.currentText(),
                                                           'Name', self.currentSelectedRowPkValue)
            if result:
                self.statusBar.setStatus('Row deleted from database successfully', StatusColor.Green)
            else:
                self.statusBar.setStatus('Failed to delete row from database', StatusColor.Red)

            self.updateTableViewFrame()

    def createParameterMappingUI(self):
        if not self.isDbConnectionValid():
            return
        tablesColumns = []
        for table in self.dbTableList:
            unfilteredColumns = self.mySqlQuery.getTableColumns(table)
            filteredColumns = []
            for col in unfilteredColumns:
                if col not in permanentParams + self.supplierParams and \
                        col not in ['Description', 'Manufacturer', 'Manufacturer Part Number']:
                    filteredColumns.append(col)
            tablesColumns.append(filteredColumns)
        self.dbParamsGroupBox = ParameterMappingGroupBox(self.dbTableList, tablesColumns, ['Digi-Key'])
        self.settingsTopRightVLayout.takeAt(1)
        self.settingsTopRightVLayout.addWidget(self.dbParamsGroupBox)
        self.settingsTopRightVLayout.addStretch(1)


if __name__ == "__main__":
    App()
