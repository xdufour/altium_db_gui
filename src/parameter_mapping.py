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

        loadedDict = loadFromJson(jsonFile)

        for supplier in supplierList:
            self.paramsDicts[supplier] = {}
            for i, table in enumerate(tableList):
                self.paramsDicts[supplier][table] = loadedDict.get(supplier, {}).get(table, {})
                for dbParam in tableColumnsList[i]:
                    self.paramsDicts[supplier][table][dbParam] = loadedDict.get(supplier, {}).get(table, {}).get(dbParam, dbParam)

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
        self.mainGridLayout.addWidget(self.tableListComboBox, self.comboBoxRow, self.dbParamsColumn + 1)

        self.supplierTableLabel = QLabel("Supplier:")
        self.mainGridLayout.addWidget(self.supplierTableLabel, self.comboBoxRow, self.supplierParamsColumn)

        self.supplierListComboBox = QComboBox()
        self.supplierListComboBox.addItems(supplierList)
        self.supplierListComboBox.currentTextChanged.connect(self.updateTableMappingFields)
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
        supplier = self.supplierListComboBox.currentText()
        table = self.tableListComboBox.currentText()

        for label in labels:
            label.deleteLater()
        labels.clear()
        for k in lineEdits:
            lineEdits[k].deleteLater()
        lineEdits.clear()

        self.mainGridLayout.takeAt(self.mainGridLayout.indexOf(self.saveButton))

        for param in self.tableColumnsList[self.tableListComboBox.currentIndex()]:
            dbLineEdit = QLineEdit(param)
            dbLineEdit.setReadOnly(True)
            lineEdits[param] = dbLineEdit
            self.mainGridLayout.addWidget(dbLineEdit, row, self.dbParamsColumn, 1, 2)

            supplierLineEdit = QLineEdit()
            try:
                supplierLineEdit.setText(self.paramsDicts[supplier][table][param])
            except KeyError:
                # New table was added in database that does not have paramater mapping yet
                supplierLineEdit.setText('')

            supplierLineEdit.textChanged.connect(lambda: self.saveButton.setEnabled(True))
            supplierLineEdit.textChanged.connect(lambda string, t=table, s=supplier, p=param:
                                                 utils.assignToDict(self.paramsDicts[s][t],
                                                                    lineEdits[p].text(),
                                                                    string))
            lineEdits[param + "_s"] = supplierLineEdit
            self.mainGridLayout.addWidget(supplierLineEdit, row, self.supplierParamsColumn, 1, 2)

            row += 1

        self.mainGridLayout.addWidget(self.saveButton, row, self.supplierParamsColumn + 1)

    def saveCmd(self):
        saveToJson(jsonFile, self.paramsDicts)
        self.saveButton.setEnabled(False)

    def getParamsDict(self, supplier, table):
        return self.paramsDicts[supplier][table]
