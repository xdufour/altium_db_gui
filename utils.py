from PIL import Image, ImageTk
from PyQt5.QtGui import QIcon


def loadImageTk(filepath, size):
    img = Image.open(filepath)
    img.thumbnail(size=size)
    return ImageTk.PhotoImage(img)


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