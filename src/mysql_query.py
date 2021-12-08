from mysql.connector import connection
from mysql.connector.errors import ProgrammingError


def init(user, password, address, database):
    cnx = connection.MySQLConnection(user=user, password=password,
                                     host=address,
                                     database=database,
                                     auth_plugin='mysql_native_password',
                                     connect_timeout=1000)
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


def insertInDatabase(cnx, table, headers, data):
    cursor = cnx.cursor()
    query = 'INSERT INTO `altium_db_library`.`' + table + "` ("
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
    except ProgrammingError:
        print("SQL Query Insert Failure")


class MySqlEditQueryData:
    def __init__(self, columnName, value, primaryKey, pkValue):
        self.columnNames = []
        self.values = []
        self.columnNames.append(columnName)
        self.values.append(value)
        self.primaryKey = primaryKey
        self.pkValue = pkValue
        print(f"Pending update query created: {columnName} = {value} for primaryKey {primaryKey} = {pkValue}")

    def append(self, columnName, value):
        self.columnNames.append(columnName)
        self.values.append(value)
        print(f"Pending update created amended: {columnName} = {value} for primaryKey {self.primaryKey} = {self.pkValue}")


def editDatabase(cnx, db, table, editList):
    cursor = cnx.cursor()
    for edit in editList:
        query = "UPDATE `" + db + "`.`" + table + "` SET "  # TODO: Refactor to use escape sequences (prevent injection)
        for columnName, value in zip(edit.columnNames, edit.values):
            query += "`" + columnName + "` = '" + value + "', "
        query = query[:len(query) - 2]
        query += " WHERE (`" + edit.primaryKey + "` = '" + edit.pkValue + "')"
        print("SQL Query: " + query)
        try:
            cursor.execute(query)
            cnx.commit()
            print(cursor.rowcount, " row(s) affected")
        except ProgrammingError:
            print("SQL Query Update Failure")


def deleteRowFromDatabase(cnx, db, table, primaryKey, pkValue):
    cursor = cnx.cursor()
    query = f"DELETE FROM `{db}`.`{table}` WHERE `{primaryKey}` = '{pkValue}'"
    print(f"SQL Query: {query}")
    try:
        cursor.execute(query)
        cnx.commit()
        print(cursor.rowcount, " row(s) deleted")
    except ProgrammingError:
        print("SQL Query Update Failure")
