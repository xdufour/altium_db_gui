import json

mysql_login_filename = 'mysql_server_login.json'
lib_search_path_filename = 'lib_search_path.json'


def saveToJson(file, data):
    jsonObject = json.dumps(data, indent=4)
    with open(file, "w") as outfile:
        outfile.write(jsonObject)
    print("File " + file + " written:")
    print(data)


def loadFromJson(file):
    jsonData = {}
    try:
        with open(file, 'r') as openfile:
            jsonData = json.load(openfile)
        print("Loaded data from file " + file + ":")
        print(jsonData)
    except FileNotFoundError:
        print("File " + file + " not found")
    return jsonData
