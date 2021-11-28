from PyQt5.QtGui import QIcon


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
