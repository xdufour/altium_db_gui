from PIL import Image, ImageTk
from PyQt5.QtGui import QIcon


def loadImageTk(filepath, size):
    img = Image.open(filepath)
    img.thumbnail(size=size)
    return ImageTk.PhotoImage(img)


def loadQIcon(filepath):
    return QIcon(filepath)
