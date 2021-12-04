from PyQt5.QtGui import QIcon
import os


def loadQIcon(filepath):
    return QIcon(filepath)


def dictHasEmptyValue(d):
    for k in d:
        if d[k] == "":
            return True
    return False


def strippedList(srcList, unwantedList):
    dstList = []
    for it in srcList:
        if it not in unwantedList:
            dstList.append(it)
    return dstList


def columnMax(array2d, index):
    maxVal = 0
    for row in array2d:
        maxVal = max(maxVal, row[index])
    return maxVal


def getFieldText(widget):
    if widget.metaObject().className() == "QLineEdit":
        return widget.text()
    elif widget.metaObject().className() == "QComboBox":
        return widget.currentText()


def setLineEditValidationState(lineEdit, state):
    lineEdit.setProperty('valid', state)
    lineEdit.style().unpolish(lineEdit)
    lineEdit.style().unpolish(lineEdit)
    lineEdit.repaint()


def assignToDict(_dict, key, value):
    _dict[key] = value


def createFolderIfNotExists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
