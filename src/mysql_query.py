from mysql.connector import connection
from mysql.connector.errors import ProgrammingError, OperationalError, InterfaceError


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
        print(
            f"Pending update created amended: {columnName} = {value} for primaryKey {self.primaryKey} = {self.pkValue}")


class MySQLQuery:
    def __init__(self, user, password, address, database):
        self.cnx = None
        try:
            self.cnx = connection.MySQLConnection(user=user, password=password,
                                                  host=address,
                                                  database=database,
                                                  auth_plugin='mysql_native_password',
                                                  connect_timeout=1)
        except ProgrammingError:
            print("MySQL Server Connection Error: Access Denied")
        except OperationalError:
            print("MySQL Server Connection Error: Unable to reach server")
        except InterfaceError as e:
            if e.errno == 2003:
                print("MySQL Server Connection Error: Timed out")
            else:
                print(f"MySQL Server Connection Error: Unknown (#{e.errno})")

    def isConnected(self, attemptReconnect=True):
        connected = False
        if self.cnx is not None:
            connected = self.cnx.is_connected()
            if not connected:
                if attemptReconnect:
                    try:
                        self.cnx.connect()
                        connected = True
                    except InterfaceError:
                        print("MySQL Server Connection: Failed to reconnect automatically")
        return connected

    def getDatabaseTables(self):
        dbTableList = []
        cursor = self.cnx.cursor()
        query = "SHOW TABLES FROM `altium_db_library`"
        print("SQL Query: " + query)
        cursor.execute(query)
        for table in cursor:
            dbTableList.append(table[0])
        return dbTableList

    def getTableColumns(self, table):
        dbTableColumnList = []
        cursor = self.cnx.cursor()
        query = "SHOW COLUMNS FROM `altium_db_library`.`" + table + "`"
        print("SQL Query: " + query)
        cursor.execute(query)
        for column in cursor:
            dbTableColumnList.append(column[0])
        return dbTableColumnList

    def getTableData(self, table):
        cursor = self.cnx.cursor()
        query = "SELECT * FROM `altium_db_library`.`" + table + "`"
        print("SQL Query: " + query)
        cursor.execute(query)
        return cursor.fetchall()

    def insertInDatabase(self, table, headers, data):
        cursor = self.cnx.cursor()
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
            self.cnx.commit()
            print(cursor.rowcount, " record inserted")
        except ProgrammingError:
            print("SQL Query Insert Failure")

    def editDatabase(self, db, table, editList):
        cursor = self.cnx.cursor()
        for edit in editList:
            query = "UPDATE `" + db + "`.`" + table + "` SET "  # TODO: Refactor to use escape sequences (prevent injection)
            for columnName, value in zip(edit.columnNames, edit.values):
                query += "`" + columnName + "` = '" + value + "', "
            query = query[:len(query) - 2]
            query += " WHERE (`" + edit.primaryKey + "` = '" + edit.pkValue + "')"
            print("SQL Query: " + query)
            try:
                cursor.execute(query)
                self.cnx.commit()
                print(cursor.rowcount, " row(s) affected")
            except ProgrammingError:
                print("SQL Query Update Failure")

    def deleteRowFromDatabase(self, db, table, primaryKey, pkValue):
        cursor = self.cnx.cursor()
        query = f"DELETE FROM `{db}`.`{table}` WHERE `{primaryKey}` = '{pkValue}'"
        print(f"SQL Query: {query}")
        try:
            cursor.execute(query)
            self.cnx.commit()
            print(cursor.rowcount, " row(s) deleted")
        except ProgrammingError:
            print("SQL Query Update Failure")
