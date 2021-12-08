from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox, QGroupBox, QPushButton, QGridLayout
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5 import QtGui
from json_appdata import *
import utils

labels = []
lineEdits = {}

jsonFile = 'supplier_parameter_mapping.json'


class ParameterMappingGroupBox(QGroupBox):
    def __init__(self, tableList, tableColumnsList, supplierList):
        super().__init__("Parameter mapping")

        self.tableColumnsList = tableColumnsList
        self.paramsDicts = {}

        fm = QFontMetrics(QFont(QtGui.QGuiApplication.font().family(), QtGui.QGuiApplication.font().pointSize()))
        self.textHeight = fm.boundingRect("Text").height()

        for i, table in enumerate(tableList):
            self.paramsDicts[table] = {}
            for dbColumnName in tableColumnsList[i]:
                self.paramsDicts[table][dbColumnName] = dbColumnName

        self.dbParamsColumn = 0
        self.equalsLabelColumn = 2
        self.supplierParamsColumn = 3

        self.comboBoxRow = 0
        self.labelRow = 1
        self.fieldsRow = 2

        self.mainGridLayout = QGridLayout()
        self.setLayout(self.mainGridLayout)

        self.dbTableLabel = QLabel("Database Table:")
        self.mainGridLayout.addWidget(self.dbTableLabel, self.comboBoxRow, self.dbParamsColumn)

        self.tableListComboBox = QComboBox()
        self.tableListComboBox.addItems(tableList)
        self.tableListComboBox.setCurrentIndex(0)
        self.tableListComboBox.currentTextChanged.connect(self.updateTableMappingFields)
        self.tableListComboBox.currentTextChanged.connect(lambda: self.saveButton.setEnabled(False))
        self.mainGridLayout.addWidget(self.tableListComboBox, self.comboBoxRow, self.dbParamsColumn + 1)

        self.supplierTableLabel = QLabel("Supplier:")
        self.mainGridLayout.addWidget(self.supplierTableLabel, self.comboBoxRow, self.supplierParamsColumn)

        self.supplierListComboBox = QComboBox()
        self.supplierListComboBox.addItems(supplierList)
        self.mainGridLayout.addWidget(self.supplierListComboBox, self.comboBoxRow, self.supplierParamsColumn + 1)
        self.mainGridLayout.setSpacing(self.textHeight * 0.6)
        self.mainGridLayout.setColumnMinimumWidth(2, self.textHeight * 3)

        self.dbParamLabel = QLabel("Database Field Name")
        self.mainGridLayout.addWidget(self.dbParamLabel, self.labelRow, self.dbParamsColumn)

        self.supParamLabel = QLabel("Supplier Parameter")
        self.mainGridLayout.addWidget(self.supParamLabel, self.labelRow, self.supplierParamsColumn)

        self.saveButton = QPushButton("Save")
        self.saveButton.setEnabled(False)
        self.saveButton.setProperty('accent', True)
        self.saveButton.released.connect(self.saveCmd)
        self.mainGridLayout.addWidget(self.saveButton, self.fieldsRow, self.supplierParamsColumn + 1)

        self.updateTableMappingFields()

    def updateTableMappingFields(self):
        row = self.fieldsRow

        for label in labels:
            label.deleteLater()
        labels.clear()
        for k in lineEdits:
            lineEdits[k].deleteLater()
        lineEdits.clear()

        configDict = loadFromJson(jsonFile)
        if len(configDict) > 0:
            self.paramsDicts = configDict

        self.mainGridLayout.takeAt(self.mainGridLayout.indexOf(self.saveButton))

        for columnName in self.tableColumnsList[self.tableListComboBox.currentIndex()]:
            dbLineEdit = QLineEdit(columnName)
            dbLineEdit.setReadOnly(True)
            lineEdits[columnName] = dbLineEdit
            self.mainGridLayout.addWidget(dbLineEdit, row, self.dbParamsColumn, 1, 2)

            supplierLineEdit = QLineEdit()
            supplierLineEdit.setText(self.paramsDicts[self.tableListComboBox.currentText()][columnName])
            supplierLineEdit.textChanged.connect(lambda: self.saveButton.setEnabled(True))
            supplierLineEdit.textChanged.connect(lambda s, t=self.tableListComboBox.currentText(), c=columnName:
                                                 utils.assignToDict(self.paramsDicts[t], lineEdits[c].text(), s))
            lineEdits[columnName + "_s"] = supplierLineEdit
            self.mainGridLayout.addWidget(supplierLineEdit, row, self.supplierParamsColumn, 1, 2)

            row += 1

        self.mainGridLayout.addWidget(self.saveButton, row, self.supplierParamsColumn + 1)

    def saveCmd(self):
        saveToJson(jsonFile, self.paramsDicts)
        self.saveButton.setEnabled(False)

    def getParamsDict(self):
        return self.paramsDicts
