import subprocess
from PyQt5.QtGui import QIcon
import os
import re
from subprocess import PIPE


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
    lineEdit.style().polish(lineEdit)
    lineEdit.repaint()


def assignToDict(_dict, key, value):
    _dict[key] = value


def createFolderIfNotExists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def matchFromList(pattern, strList) -> list:
    result = []
    for s in strList:
        m = re.match(pattern, s)
        if m:
            result.append(m.group())
    return result


def strReplaceMultiple(string: str, charList, charNew) -> str:
    newStr = string
    for c in charList:
        newStr = newStr.replace(c, charNew)
    return newStr


def ping(address: str, timeout=1000) -> bool:
    result = subprocess.run(["ping", "-n", "1", "-w", f"{timeout}", address],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            creationflags=0x08000000,
                            text=True)
    response = result.stdout
    if "re‡us = 1" in response or "Received = 1" in response:
        print(f"Ping to {address} successful")
        return True
    else:
        print(f"Ping to {address} unsuccessful")
        return False
