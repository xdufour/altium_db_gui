import json

mysql_login_filename = 'mysql_server_login.json'
lib_search_path_filename = 'lib_search_path.json'


def saveToJson(file, dataDict):
    jsonObject = json.dumps(dataDict, indent=4)
    with open(file, "w") as outfile:
        outfile.write(jsonObject)
    print("File " + file + " written:")
    print(dict)


def loadFromJson(file):
    jsonDict = {}
    try:
        with open(file, 'r') as openfile:
            jsonDict = json.load(openfile)
        print("Loaded data from file " + file + ":")
        print(jsonDict)
    except FileNotFoundError:
        print("File " + file + " not found")
    return jsonDict