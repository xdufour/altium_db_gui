from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox, QGroupBox, QPushButton, QGridLayout
from PyQt5.QtCore import Qt
import json_appdata
import mysql_query

labels = []
lineEdits = []


class ParameterMappingGroupBox(QGroupBox):
    def __init__(self, tableList, tableColumnsList, supplierList):
        super().__init__("Parameter mapping")

        self.tableColumnsList = tableColumnsList

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
        self.mainGridLayout.addWidget(self.supplierListComboBox, self.comboBoxRow, self.supplierParamsColumn + 1)
        self.mainGridLayout.setSpacing(20)
        self.mainGridLayout.setColumnMinimumWidth(2, 100)

        self.dbParamLabel = QLabel("Database Field Name")
        self.mainGridLayout.addWidget(self.dbParamLabel, self.labelRow, self.dbParamsColumn)

        self.supParamLabel = QLabel("Supplier Parameter")
        self.mainGridLayout.addWidget(self.supParamLabel, self.labelRow, self.supplierParamsColumn)

        self.saveButton = QPushButton("Save")
        self.saveButton.setEnabled(False)
        self.mainGridLayout.addWidget(self.saveButton, self.fieldsRow, self.supplierParamsColumn + 1)

        self.updateTableMappingFields()

    def updateTableMappingFields(self):
        row = self.fieldsRow

        for label in labels:
            label.deleteLater()
        labels.clear()
        for supplierLineEdit in lineEdits:
            supplierLineEdit.deleteLater()
        lineEdits.clear()

        self.mainGridLayout.takeAt(self.mainGridLayout.indexOf(self.saveButton))

        for columnName in self.tableColumnsList[self.tableListComboBox.currentIndex()]:
            dbLineEdit = QLineEdit(columnName)
            dbLineEdit.setReadOnly(True)
            lineEdits.append(dbLineEdit)
            self.mainGridLayout.addWidget(dbLineEdit, row, self.dbParamsColumn, 1, 2)

            supplierLineEdit = QLineEdit()
            supplierLineEdit.setText(columnName)  # TODO: load json and change if exists
            supplierLineEdit.textChanged.connect(lambda: self.saveButton.setEnabled(True))
            lineEdits.append(supplierLineEdit)
            self.mainGridLayout.addWidget(supplierLineEdit, row, self.supplierParamsColumn, 1, 2)
            row += 1

        self.mainGridLayout.addWidget(self.saveButton, row, self.supplierParamsColumn + 1)
