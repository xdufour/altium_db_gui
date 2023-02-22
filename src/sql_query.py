from mysql.connector import connection
from mysql.connector.errors import ProgrammingError, OperationalError, InterfaceError
from mysql.connector.locales.eng import client_error
import mariadb as mdb
import utils


class SQLEditQueryData:
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


# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class SQLDB:
    def __init__(self, user, password, address, database, rdbms):
        self.user = user
        self.db = database
        self.address = address
        self.rdbms = rdbms
        self.cnx = None
        self.errorMsg = ""

        if not utils.ping(self.address, 500):
            self.errorMsg = "MySQL Server Connection: Host offline"
            return
        if rdbms == 'MySQL':
            self.mySQLConnect(user, password, address, database)
        elif rdbms == 'MariaDB':
            self.mariaDBConnect(user, password, address, database)

    def mySQLConnect(self, user, password, address, database):
        try:
            self.cnx = connection.MySQLConnection(user=user, password=password,
                                                  host=address,
                                                  database=database,
                                                  auth_plugin='mysql_native_password',
                                                  connect_timeout=1)
            self.getUserGrants()
            return
        except ProgrammingError:
            self.errorMsg = "MySQL Server Connection Error: Access Denied"
        except OperationalError:
            self.errorMsg = "MySQL Server Connection Error: Unable to reach server"
        except InterfaceError as e:
            if e.errno == 2003:
                self.errorMsg = "MySQL Server Connection Error: Timed out"
            else:
                self.errorMsg = "MySQL Server Connection Error: Unknown (#{e.errno})"
        print(self.errorMsg)

    def mariaDBConnect(self, user, password, address, database):
        try:
            self.cnx = mdb.connect(
                user=user,
                password=password,
                host=address,
                database=database)
            self.getUserGrants()
            return
        except mdb.Error as e:
            print(f"MariaDB Server Connection Error: {e}")

    def isConnected(self, attemptReconnect=True):
        connected = False
        if self.cnx is not None:
            try:
                if self.rdbms == 'MySQL': self.cnx.reconnect(int(attemptReconnect))
                elif self.rdbms == 'MariaDB': self.cnx.reconnect()
                connected = True
            except (InterfaceError, mdb.Error) as e:
                self.errorMsg = "MySQL Server Connection: Lost connection"
                if attemptReconnect:
                    self.errorMsg += ", failed to reconnect automatically"
                print(self.errorMsg)
                if not utils.ping(self.address, 250):
                    self.errorMsg += " (Host offline)"
                    return connected
        return connected

    def getErrorMessage(self):
        return self.errorMsg

    def getUserGrants(self):
        cursor = self.cnx.cursor()
        query = f"SHOW GRANTS FOR `{self.user}`@`%`;"
        cursor.execute(query)
        result = str(cursor.fetchone())
        result = result.replace("('GRANT ", "").replace(f"ON *.* TO `{self.user}`@`%`',)", "")
        grants = result.split(', ')
        return grants

    def getDatabaseTables(self):
        dbTableList = []
        cursor = self.cnx.cursor()
        query = f"SHOW TABLES FROM `{self.db}`"
        print("SQL Query: " + query)
        cursor.execute(query)
        for table in cursor:
            dbTableList.append(table[0])
        return dbTableList

    def getTableColumns(self, table):
        dbTableColumnList = []
        cursor = self.cnx.cursor()
        query = f"SHOW COLUMNS FROM `{self.db}`.`{table}`"
        print("SQL Query: " + query)
        cursor.execute(query)
        for column in cursor:
            dbTableColumnList.append(column[0])
        return dbTableColumnList

    def getTableData(self, table):
        cursor = self.cnx.cursor()
        query = f"SELECT * FROM `{self.db}`.`{table}`"
        print("SQL Query: " + query)
        cursor.execute(query)
        return cursor.fetchall()

    def insertInDatabase(self, table, headers, data):
        cursor = self.cnx.cursor()
        result = False
        query = f"INSERT INTO `{self.db}`.`{table}` ("
        for h in headers:
            query += "`" + h + "`, "
        query = query[:len(query) - 2]
        query += ") VALUES ("
        for _ in data:
            query += "%s, "
        query = query[:len(query) - 2]
        query += ")"
        print("SQL Query:" + query)
        try:
            cursor.execute(query, data)
            self.cnx.commit()
            print(cursor.rowcount, " record inserted")
            result = cursor.rowcount
        except ProgrammingError:
            self.errorMsg = "SQL Query Insert Failure"
            print(self.errorMsg)
        return result

    def editDatabase(self, table, editList):
        cursor = self.cnx.cursor()
        result = True
        for edit in editList:
            query = f"UPDATE `{self.db}`.`{table}` SET "
            for columnName in edit.columnNames:
                query += "`" + columnName + "` = %s, "
            query = query[:len(query) - 2]
            query += " WHERE (`" + edit.primaryKey + "` = '" + edit.pkValue + "')"
            print("SQL Query: " + query)
            try:
                cursor.execute(query, edit.values)
                self.cnx.commit()
                print(cursor.rowcount, " row(s) affected")
                if cursor.rowcount < 1:
                    result = False
            except ProgrammingError:
                self.errorMsg = "SQL Query Update Failure"
                print(self.errorMsg)
                result = False
        return result

    def deleteRowFromDatabase(self, table, primaryKey, pkValue):
        cursor = self.cnx.cursor()
        result = False
        query = f"DELETE FROM `{self.db}`.`{table}` WHERE `{primaryKey}` = '{pkValue}'"
        print(f"SQL Query: {query}")
        try:
            cursor.execute(query)
            self.cnx.commit()
            print(cursor.rowcount, " row(s) deleted")
            result = cursor.rowcount
        except ProgrammingError:
            self.errorMsg = f"SQL Query Deletion Failure"
            print(self.errorMsg)
        return result
