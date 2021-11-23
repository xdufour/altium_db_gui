import tkinter
import TKinterModernThemes as TKMT
from tkinter import ttk
import dk_api
import mysql_query
import json_appdata
import mysql.connector
from PIL import Image, ImageTk

permanentParams = ["Name", "Supplier 1", "Supplier Part Number 1", "Library Path",
                    "Library Ref", "Footprint Path", "Footprint Ref"]


def getDbTableList(mysql_cnx):
    dbTableList = []
    dbTableCursor = mysql_query.getDatabaseTables(mysql_cnx)
    for it in dbTableCursor:
        dbTableList.append(it[0])
    return dbTableList


def strippedList(srcList, unwantedList):
    dstList = []
    for it in srcList:
        if it not in unwantedList:
            dstList.append(it)
    return dstList


class App(TKMT.ThemedTKinterFrame):
    def __init__(self, theme, mode, usecommandlineargs=False, usethemeconfigfile=False):
        super().__init__(str("Altium DB GUI"), theme, mode, usecommandlineargs, usethemeconfigfile)

        self.loginInfoDict = {
            "address": "",
            "user": "",
            "password": "",
            "database": ""
        }

        def loadGUI(event):
            dbColumnList = mysql_query.getTableColumns(self.cnx, table_cbox.get().lower())
            row = 2
            # Delete any previously created widgets
            for column in self.dbColumnNames:
                if column not in permanentParams:
                    self.root.nametowidget(".nbk.f_home." + column.lower()).destroy()
                    self.root.nametowidget(".nbk.f_home." + column.lower() + "_l").destroy()
            self.dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnList):
                self.dbColumnNames.append(column[0])
                if self.dbColumnNames[i] not in permanentParams:
                    label = ttk.Label(f_home, text=self.dbColumnNames[i] + ":", name=(self.dbColumnNames[i].lower() + "_l"))
                    label.grid(row=row, column=0, padx=10, pady=10, sticky='nsew')
                    entry = ttk.Entry(f_home, name=self.dbColumnNames[i].lower())
                    entry.grid(row=row, column=1, padx=10, pady=10, sticky='nsew')
                    row = row + 1
            print(f"Loaded GUI for {table_cbox.get()}")

        def query_supplier_event(event):
            query_supplier()

        def query_supplier():
            dkpn = supplier_pn_entry.get()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, table_cbox.get(), strippedList(self.dbColumnNames, permanentParams))
            print(result)
            for it in result:
                try:
                    self.root.nametowidget(".nbk.f_home." + it[0].lower()).delete(0, 255)
                    self.root.nametowidget(".nbk.f_home." + it[0].lower()).insert(0, it[1])
                except KeyError:
                    print(f"No widget named {it[0].lower()}")

        def addToDatabaseBtn():
            rowData = []
            for col in self.dbColumnNames:
                try:
                    rowData.append(self.root.nametowidget(".nbk.f_home." + col.lower()).get())
                except KeyError:
                    print(f"No widget named {col.lower()}")
            mysql_query.insertInDatabase(self.cnx, table_cbox.get().lower(), self.dbColumnNames, rowData)

        def validateName(inp):
            if len(inp) > 0:
                db_button["state"] = "normal"
            else:
                db_button["state"] = "disabled"
            return True
        valNameCmd = self.root.register(validateName)

        def getDbLogins():
            self.loginInfoDict = json_appdata.getDatabaseLoginInfo()
            login_address_entry.insert(0, self.loginInfoDict['address'])
            login_user_entry.insert(0, self.loginInfoDict['user'])
            login_password_entry.insert(0, self.loginInfoDict['password'])
            login_db_name_entry.insert(0, self.loginInfoDict['database'])

        def saveDbLogins():
            json_appdata.saveDatabaseLoginInfo(login_address_entry.get(),
                                                login_user_entry.get(),
                                                login_password_entry.get(),
                                                login_db_name_entry.get())

        def loadDbTables():
            self.dbTableList = getDbTableList(self.cnx)
            table_cbox['values'] = self.dbTableList
            table_cbox.current(0)

        def testDbConnection():
            if not self.connected and login_user_entry.get() and login_password_entry and login_address_entry and login_db_name_entry:
                try:
                    self.cnx = mysql_query.init(login_user_entry.get(),
                                                login_password_entry.get(),
                                                login_address_entry.get(),
                                                login_db_name_entry.get())
                    if self.cnx.is_connected:
                        self.connected = True
                        loadDbTables()
                        loadGUI(0)
                        login_test_button.configure(state="disabled")
                        notebook.tab(0, state='normal')
                except mysql.connector.errors.ProgrammingError:
                    print("Access Denied")
                except mysql.connector.errors.InterfaceError:
                    print("Invalid Login Information Format")
            if not self.connected:
                notebook.tab(0, state='disabled')

        self.connected = False

        img_home = Image.open('home.png')
        img_home.thumbnail(size=(32, 32))
        ph_home = ImageTk.PhotoImage(img_home)
        img_settings = Image.open('settings.png')
        img_settings.thumbnail(size=(32, 32))
        ph_settings = ImageTk.PhotoImage(img_settings)

        self.dbTableList = []
        self.dbColumnNames = []

        # Create styles
        style = ttk.Style(self.master)
        style.configure('lefttab.TNotebook', tabposition='wn', tabmargins=[-10, -5, -16, 0])
        style.configure('lefttab.TNotebook.Tab', padding=[0, 0])

        notebook = ttk.Notebook(self.master, style='lefttab.TNotebook', name="nbk")
        notebook.grid(row=0, column=0, rowspan=5, columnspan=5, padx=0, pady=0, sticky='nsew')
        f_home = ttk.Frame(notebook, name="f_home")
        f_settings = ttk.Frame(notebook, name="f_settings")
        f_home.pack(fill='both', expand=True)
        f_settings.pack(fill='both', expand=True)

        notebook.add(f_home, image=ph_home, compound=tkinter.TOP)
        notebook.add(f_settings, image=ph_settings, compound=tkinter.TOP)

        # Settings page widgets
        f_login = ttk.LabelFrame(f_settings, text="MySQL Server Login", name="f_login")
        f_login.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        db_address_label = ttk.Label(f_login, text="Address:")
        db_address_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        login_address_entry = ttk.Entry(f_login, name="db address entry")
        login_address_entry.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        db_user_label = ttk.Label(f_login, text="User:")
        db_user_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        login_user_entry = ttk.Entry(f_login, name="db user entry")
        login_user_entry.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        db_password_label = ttk.Label(f_login, text="Password:")
        db_password_label.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
        login_password_entry = ttk.Entry(f_login, name="db password entry")
        login_password_entry.grid(row=2, column=1, padx=10, pady=10, sticky='nsew')

        db_name_label = ttk.Label(f_login, text="Database:")
        db_name_label.grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
        login_db_name_entry = ttk.Entry(f_login, name="db name entry")
        login_db_name_entry.grid(row=3, column=1, padx=10, pady=10, sticky='nsew')

        login_test_button = ttk.Button(f_login, width=16, text="Test", command=testDbConnection)
        login_test_button.grid(row=4, column=0, padx=10, pady=10, sticky='nsew')

        # Home page widgets
        table_label = ttk.Label(f_home, text="DB Table:")
        table_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        table_cbox = ttk.Combobox(f_home, state="readonly")
        table_cbox.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        table_cbox.bind("<<ComboboxSelected>>", loadGUI)

        getDbLogins()
        testDbConnection()

        db_button = ttk.Button(f_home, text="Add to database", command=addToDatabaseBtn)
        db_button.grid(row=0, column=3, padx=10, pady=10, sticky='nsew')
        db_button["state"] = "disabled"

        name_label = ttk.Label(f_home, text="Name:")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        name_entry = ttk.Entry(f_home, name="name", validate="all", validatecommand=(valNameCmd, '%P'))
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        supplier_label = ttk.Label(f_home, text="Supplier 1:")
        supplier_label.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox = ttk.Combobox(f_home, state="readonly", name="supplier 1")
        supplier_cbox.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')
        supplier_cbox['values'] = "Digi-Key"
        supplier_cbox.current(0)

        supplier_pn_label = ttk.Label(f_home, text="Supplier Part Number 1:")
        supplier_pn_label.grid(row=2, column=2, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry = ttk.Entry(f_home, name="supplier part number 1")
        supplier_pn_entry.grid(row=2, column=3, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry.bind("<Return>", query_supplier_event)

        supplier_button = ttk.Button(f_home, text="Autofill", command=query_supplier)
        supplier_button.grid(row=2, column=4, padx=10, pady=10, sticky='nsew')

        library_path_label = ttk.Label(f_home, text="Library Path" + ":")
        library_path_label.grid(row=3, column=2, padx=10, pady=10, sticky='nsew')
        library_path_entry = ttk.Entry(f_home, name="library path")
        library_path_entry.grid(row=3, column=3, padx=10, pady=10, sticky='nsew')

        library_ref_label = ttk.Label(f_home, text="Library Ref" + ":")
        library_ref_label.grid(row=4, column=2, padx=10, pady=10, sticky='nsew')
        library_ref_entry = ttk.Entry(f_home, name="library ref")
        library_ref_entry.grid(row=4, column=3, padx=10, pady=10, sticky='nsew')

        footprint_path_label = ttk.Label(f_home, text="Footprint Path" + ":")
        footprint_path_label.grid(row=5, column=2, padx=10, pady=10, sticky='nsew')
        footprint_path_entry = ttk.Entry(f_home, name="footprint path")
        footprint_path_entry.grid(row=5, column=3, padx=10, pady=10, sticky='nsew')

        footprint_ref_label = ttk.Label(f_home, text="Footprint Ref" + ":")
        footprint_ref_label.grid(row=6, column=2, padx=10, pady=10, sticky='nsew')
        footprint_ref_entry = ttk.Entry(f_home, name="footprint ref")
        footprint_ref_entry.grid(row=6, column=3, padx=10, pady=10, sticky='nsew')

        db_save_button= ttk.Button(f_login, text="Save", command=saveDbLogins)
        db_save_button.grid(row=4, column=1, padx=10, pady=10, sticky='nsew')

        self.run()


if __name__ == "__main__":
    App(str("sun-valley"), str("dark"))
