import json
import os
from utils import createFolderIfNotExists

path = os.getenv('APPDATA')
folder = '\\altium DB GUI\\json\\'


def saveToJson(file, data):
    jsonObject = json.dumps(data, indent=4)
    createFolderIfNotExists(path + folder)
    with open(path + folder + file, "w") as outfile:
        outfile.write(jsonObject)
    print("File " + path + folder + file + " written:")
    print(data)


def loadFromJson(file):
    jsonData = {}
    try:
        with open(path + folder + file, 'r') as openfile:
            jsonData = json.load(openfile)
        print("Loaded data from file " + path + folder + file + ":")
        print(jsonData)
    except FileNotFoundError:
        print("File " + path + folder + file + " not found")
    return jsonData
