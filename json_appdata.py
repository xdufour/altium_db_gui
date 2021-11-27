import json

mysql_login_filename = 'mysql_server_login.json'
lib_search_path_filename = 'lib_search_path.json'


def saveDatabaseLoginInfo(address, user, password, database):
    data_dict = {
        "address": address,
        "user": user,
        "password": password,
        "database": database
    }
    json_object = json.dumps(data_dict, indent=4)
    with open(mysql_login_filename, "w") as outfile:
        outfile.write(json_object)
    print("File " + mysql_login_filename + " written:")
    print(data_dict)


def getDatabaseLoginInfo():
    json_object = {
        "address": "",
        "user": "",
        "password": "",
        "database": ""
    }
    try:
        with open(mysql_login_filename, 'r') as openfile:
            json_object = json.load(openfile)
        print("Loaded login info from json file:")
        print(json_object)
    except FileNotFoundError:
        print("MySQL login information not configured")
    return json_object


def saveLibrarySearchPath(path):
    data_dict = {
        "filepath": path
    }
    json_object = json.dumps(data_dict, indent=4)
    with open(lib_search_path_filename, "w") as outfile:
        outfile.write(json_object)
    print("File " + lib_search_path_filename + " written:")
    print(data_dict)


def getLibrarySearchPath():
    json_object = {}
    try:
        with open(lib_search_path_filename, 'r') as openfile:
            json_object = json.load(openfile)
        print("Loaded Altium search path info from json file:")
    except FileNotFoundError:
        print("MySQL login information not configured")
    return json_object
