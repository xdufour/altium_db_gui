import tkinter
import TKinterModernThemes as TKMT
from tkinter import ttk
from tkinter import filedialog
import mysql.connector
import glob
import dk_api
import mysql_query
import json_appdata
import altium_parser
import utils

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

        def browseBtn():
            dir = filedialog.askdirectory()
            if dir:
                search_path_entry.delete(0, 255)
                search_path_entry.insert(0, dir)
                print(f"New library search path set: {dir}")
                updatePathComboboxes(dir)

        def updatePathComboboxes(dirPath):
            schlibFiles = glob.glob(dirPath + '/**/*.SchLib', recursive=True)
            pcblibFiles = glob.glob(dirPath + '/**/*.PcbLib', recursive=True)
            resultSchFiles = []
            resultPcbFiles = []
            for file in schlibFiles:
                resultSchFiles.append(file[file.find('Symbols'):].replace('\\', '/', 255))
            for file in pcblibFiles:
                resultPcbFiles.append(file[file.find('Footprints'):].replace('\\', '/', 255))
            library_path_cbox['values'] = resultSchFiles
            footprint_path_cbox['values'] = resultPcbFiles

        def updateLibraryRefCombobox(inp):
            if self.libraryPathCurrentVal != inp:
                self.libraryPathCurrentVal = inp
                library_ref_cbox.delete(0, 255)
                library_ref_cbox['values'] = altium_parser.getLibraryRefList(search_path_entry.get() + '/' + inp)
            return True
        updateLibraryRefCmd = self.root.register(updateLibraryRefCombobox)

        def updateFootprintRefCombobox(inp):
            if self.footprintPathCurrentVal != inp:
                self.footprintPathCurrentVal = inp
                footprint_ref_cbox.delete(0, 255)
                footprint_ref_cbox['values'] = altium_parser.getFootprintRefList(search_path_entry.get() + '/' + inp)
            return True
        updateFootprintRefCmd = self.root.register(updateFootprintRefCombobox)

        self.connected = False
        self.dbTableList = []
        self.dbColumnNames = []

        self.root.tk.call('wm', 'iconbitmap', self.root._w, 'assets/app.ico')
        ph_home = utils.loadImageTk('assets/home.png', (32, 32))
        ph_settings = utils.loadImageTk('assets/settings.png', (32, 32))
        ph_download = utils.loadImageTk('assets/download_cloud.png', (24, 24))

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
        f_login.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')

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

        search_path_label = ttk.Label(f_settings, text="Library Search Path:")
        search_path_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        search_path_entry = ttk.Entry(f_settings)
        search_path_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='nsew')
        search_path_browse_button = ttk.Button(f_settings, text="Browse", command=browseBtn)
        search_path_browse_button.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')

        # Home page widgets
        table_label = ttk.Label(f_home, text="DB Table:")
        table_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        table_cbox = ttk.Combobox(f_home, state="readonly")
        table_cbox.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        table_cbox.bind("<<ComboboxSelected>>", loadGUI)

        getDbLogins()
        testDbConnection()

        db_button = ttk.Button(f_home, text="Add to database", command=addToDatabaseBtn)
        db_button.grid(row=0, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')
        db_button["state"] = "disabled"

        name_label = ttk.Label(f_home, text="Name:")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        name_entry = ttk.Entry(f_home, name="name", validate="all", validatecommand=(valNameCmd, '%P'))
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        supplier_label = ttk.Label(f_home, text="Supplier 1:")
        supplier_label.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox = ttk.Combobox(f_home, state="readonly", name="supplier 1")
        supplier_cbox.grid(row=1, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox['values'] = "Digi-Key"
        supplier_cbox.current(0)

        supplier_pn_label = ttk.Label(f_home, text="Supplier Part Number 1:")
        supplier_pn_label.grid(row=2, column=2, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry = ttk.Entry(f_home, name="supplier part number 1")
        supplier_pn_entry.grid(row=2, column=3, padx=(10, 0), pady=10, sticky='nsew')
        supplier_pn_entry.bind("<Return>", query_supplier_event)

        supplier_button = ttk.Button(f_home, image=ph_download, command=query_supplier)
        supplier_button.grid(row=2, column=4, padx=(10, 10), pady=10, ipady=0, sticky='nsew')

        search_path_label = ttk.Label(f_home, text="Library Path" + ":")
        search_path_label.grid(row=3, column=2, padx=10, pady=10, sticky='nsew')
        library_path_cbox = ttk.Combobox(f_home, name="library path",
                                         validate="all", validatecommand=(updateLibraryRefCmd, '%P'))
        library_path_cbox.grid(row=3, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')

        library_ref_label = ttk.Label(f_home, text="Library Ref" + ":")
        library_ref_label.grid(row=4, column=2, padx=10, pady=10, sticky='nsew')
        library_ref_cbox = ttk.Combobox(f_home, name="library ref")
        library_ref_cbox.grid(row=4, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')

        footprint_path_label = ttk.Label(f_home, text="Footprint Path" + ":")
        footprint_path_label.grid(row=5, column=2, padx=10, pady=10, sticky='nsew')
        footprint_path_cbox = ttk.Combobox(f_home, name="footprint path",
                                           validate="all", validatecommand=(updateFootprintRefCmd, '%P'))
        footprint_path_cbox.grid(row=5, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')

        footprint_ref_label = ttk.Label(f_home, text="Footprint Ref" + ":")
        footprint_ref_label.grid(row=6, column=2, padx=10, pady=10, sticky='nsew')
        footprint_ref_cbox = ttk.Combobox(f_home, name="footprint ref")
        footprint_ref_cbox.grid(row=6, column=3, columnspan=2, padx=10, pady=10, sticky='nsew')

        db_save_button= ttk.Button(f_login, text="Save", command=saveDbLogins)
        db_save_button.grid(row=4, column=1, padx=10, pady=10, sticky='nsew')

        self.run()

    libraryPathCurrentVal = ""
    footprintPathCurrentVal = ""


if __name__ == "__main__":
    App(str("sun-valley"), str("dark"))
