import json


def saveDatabaseLoginInfo(address, user, password, database):
    data_dict = {
        "address": address,
        "user": user,
        "password": password,
        "database": database
    }
    json_object = json.dumps(data_dict, indent=4)
    with open("mysql_server_login.json", "w") as outfile:
        outfile.write(json_object)
    print("File mysql_server_login.json written:")
    print(data_dict)


def getDatabaseLoginInfo():
    json_object = {
        "address": "",
        "user": "",
        "password": "",
        "database": ""
    }
    try:
        with open('mysql_server_login.json', 'r') as openfile:
            json_object = json.load(openfile)
        print("Loaded login info from json file:")
        print(json_object)
    except FileNotFoundError:
        print("MySQL login information not configured")
    return json_object
