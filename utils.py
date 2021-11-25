from PIL import Image, ImageTk


def loadImageTk(filepath, size):
    img = Image.open(filepath)
    img.thumbnail(size=size)
    return ImageTk.PhotoImage(img)
