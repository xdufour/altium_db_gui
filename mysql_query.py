from mysql.connector import (connection)


def init():
    cnx = connection.MySQLConnection(user='admin', password='pantouflu50',
                                     host='localhost',
                                     database='altium_db_library')
    return cnx


def getDatabaseColumns(cnx, table):
    cursor = cnx.cursor(buffered=True)
    query = "SHOW COLUMNS FROM `altium_db_library`.`" + table + "`"
    print("SQL Query: " + query)
    cursor.execute(query)
    return cursor


def insertInDatabase(cnx, table_name, headers, data):
    cursor = cnx.cursor()
    query = "INSERT INTO `altium_db_library`.`" + table_name + "` ("
    for h in headers:
        query += "`" + h + "`, "
    query = query[:len(query) - 2]
    query += ") VALUES ("
    for d in data:
        query += "%s, "
    query = query[:len(query) - 2]
    query += ")"
    print("SQL Query:" + query)
    cursor.execute(query, data)
    cnx.commit()
    print(cursor.rowcount, " record inserted")

