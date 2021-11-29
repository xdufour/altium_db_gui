import MySQLdb
import mysql.connector.errors
from mysql.connector import (connection)


def init(user, password, address, database):
    cnx = connection.MySQLConnection(user=user, password=password,
                                     host=address,
                                     database=database)
    return cnx


def getDatabaseTables(cnx):
    dbTableList = []
    cursor = cnx.cursor()
    query = "SHOW TABLES FROM `altium_db_library`"
    print("SQL Query: " + query)
    cursor.execute(query)
    for table in cursor:
        dbTableList.append(table[0])
    return dbTableList


def getTableColumns(cnx, table):
    dbTableColumnList = []
    cursor = cnx.cursor()
    query = "SHOW COLUMNS FROM `altium_db_library`.`" + table + "`"
    print("SQL Query: " + query)
    cursor.execute(query)
    for column in cursor:
        dbTableColumnList.append(column[0])
    return dbTableColumnList


def getTableData(cnx, table):
    cursor = cnx.cursor()
    query = "SELECT * FROM `altium_db_library`.`" + table + "`"
    print("SQL Query: " + query)
    cursor.execute(query)
    return cursor.fetchall()


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
    try:
        cursor.execute(query, data)
        cnx.commit()
        print(cursor.rowcount, " record inserted")
    except MySQLdb.ProgrammingError:
        print("SQL Query Insert Failure")


class MySqlEditQueryData:
    def __init__(self, columnName, value, primaryKey, pkValue):
        self.columnName = columnName
        self.value = value
        self.primaryKey = primaryKey
        self.pkValue = pkValue
        print(f"Pending update query created: {columnName} = {value} for primaryKey {primaryKey} = {pkValue}")


def editDatabase(cnx, table, tableName, editList):
    print("EditDB")

#UPDATE `altium_db_library`.`capacitors` SET `Tolerance` = '±10%' WHERE (`Name` = 'CAP_CER_10UF_1206_16V_X7R');