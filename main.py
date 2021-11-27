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


class App(TKMT.ThemedTKinterFrame):
    def __init__(self, theme, mode, usecommandlineargs=False, usethemeconfigfile=False):
        super().__init__(str("Altium DB GUI"), theme, mode, usecommandlineargs, usethemeconfigfile)

        self.loginInfoDict = {
            "address": "",
            "user": "",
            "password": "",
            "database": ""
        }

        self.connected = False
        self.dbTableList = []
        self.dbColumnNames = []

        def loadGUI(event):
            updateCreateComponentFrame()
            updateTableViewFrame()
            print(f"Loaded GUI for {table_cbox.get()}")

        def updateCreateComponentFrame():
            row = 2
            dbColumnListCursor = mysql_query.getTableColumns(self.cnx, table_cbox.get())
            # Delete any previously created widgets
            for column in self.dbColumnNames:
                if column not in permanentParams:
                    self.root.nametowidget(".nbk.f_home.f_cc." + column.lower()).destroy()
                    self.root.nametowidget(".nbk.f_home.f_cc." + column.lower() + "_l").destroy()
            self.dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnListCursor):
                self.dbColumnNames.append(column[0])
                if self.dbColumnNames[i] not in permanentParams:
                    label = ttk.Label(f_componentEditor, text=self.dbColumnNames[i] + ":",
                                      name=(self.dbColumnNames[i].lower() + "_l"))
                    label.grid(row=row, column=0, padx=10, pady=10, sticky='nsew')
                    entry = ttk.Entry(f_componentEditor, name=self.dbColumnNames[i].lower())
                    entry.grid(row=row, column=1, columnspan=2, padx=10, pady=10, sticky='nsew')
                    row = row + 1

        def updateTableViewFrame():
            tree = None
            hsb = None
            vsb = None
            dbDataCursor = mysql_query.getTableData(self.cnx, table_cbox.get())

            if tree is not None:
                tree.destroy()
            tree = ttk.Treeview(f_tableView, columns=self.dbColumnNames, name='f_tv',
                                height=8, selectmode='browse', show='headings')
            tree.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), rowspan=5, columnspan=5, sticky='nsew')

            tree['columns'] = self.dbColumnNames
            for c in self.dbColumnNames:
                tree.heading(c, text=c, anchor=tkinter.CENTER)
                tree.column(c, width=80, minwidth=180)

            if vsb is None:
                vsb = ttk.Scrollbar(f_tableView, orient='vertical', command=tree.yview)
                vsb.grid(row=0, column=5, padx=0, pady=10, rowspan=5, sticky='nse')
                tree.configure(yscrollcommand=vsb.set)

            if hsb is None:
                hsb = ttk.Scrollbar(f_tableView, orient='horizontal', style='accent.Horizontal.TScrollbar', command=tree.xview)
                hsb.grid(row=5, column=0, padx=10, pady=0, columnspan=5, sticky='sew')
                tree.configure(xscrollcommand=hsb.set)

            data = dbDataCursor.fetchall()
            for d in data:
                print(d)
                tree.insert(parent='', index=tkinter.END, text='', values=d)

        def query_supplier_event(event):
            query_supplier()

        def query_supplier():
            dkpn = supplier_pn_entry.get()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, table_cbox.get(), utils.strippedList(self.dbColumnNames, permanentParams))
            for it in result:
                try:
                    self.root.nametowidget(str(f_componentEditor) + it[0].lower()).delete(0, 255)
                    self.root.nametowidget(str(f_componentEditor) + it[0].lower()).insert(0, it[1])
                except KeyError:
                    print(f"Error: no field found for \'{it[0].lower()}\'")

        def addToDatabaseBtn():
            rowData = []
            for col in self.dbColumnNames:
                try:
                    rowData.append(self.root.nametowidget(str(f_componentEditor) + col.lower()).get())
                except KeyError:
                    print(f"Error: No field found for \'{col.lower()}\'")
                    return
            mysql_query.insertInDatabase(self.cnx, table_cbox.get().lower(), self.dbColumnNames, rowData)

        def validateName(inp):
            if len(inp) > 0:
                db_button["state"] = "normal"
            else:
                db_button["state"] = "disabled"
            return True

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
            directory = filedialog.askdirectory()
            if directory:
                updateSearchPath(directory)
                json_appdata.saveLibrarySearchPath(directory)

        def getLibSearchPath():
            self.searchPathDict = json_appdata.getLibrarySearchPath()
            if 'filepath' in self.searchPathDict:
                updateSearchPath(self.searchPathDict['filepath'])

        def updateSearchPath(path):
            search_path_entry.delete(0, 255)
            search_path_entry.insert(0, path)
            print(f"Library search path set: {path}")
            updatePathComboboxes(path)

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

        def updateFootprintRefCombobox(inp):
            if self.footprintPathCurrentVal != inp:
                self.footprintPathCurrentVal = inp
                footprint_ref_cbox.delete(0, 255)
                footprint_ref_cbox['values'] = altium_parser.getFootprintRefList(search_path_entry.get() + '/' + inp)
            return True

        valNameCmd = self.root.register(validateName)
        updateLibraryRefCmd = self.root.register(updateLibraryRefCombobox)
        updateFootprintRefCmd = self.root.register(updateFootprintRefCombobox)

        self.root.tk.call('wm', 'iconbitmap', self.root._w, 'assets/app.ico')
        ph_home = utils.loadImageTk('assets/home.png', (32, 32))
        ph_settings = utils.loadImageTk('assets/settings.png', (32, 32))
        ph_download = utils.loadImageTk('assets/download_cloud.png', (24, 20))

        # Create styles
        style = ttk.Style(self.master)
        style.configure('lefttab.TNotebook', tabposition='wn', tabmargins=[-10, -5, -16, 0])
        style.configure('lefttab.TNotebook.Tab', padding=[0, 0])
        style.configure('accent.Horizontal.TScrollbar', troughcolor='blue')

        notebook = ttk.Notebook(self.master, style='lefttab.TNotebook', name="nbk")
        notebook.grid(row=0, column=0, padx=0, pady=0, sticky='nsew')
        f_home = ttk.Frame(notebook, name="f_home")
        f_settings = ttk.Frame(notebook, name="f_settings")
        f_home.pack(fill='both', expand=True)
        f_settings.pack(fill='both', expand=True)

        notebook.add(f_home, image=ph_home, compound=tkinter.TOP)
        notebook.add(f_settings, image=ph_settings, compound=tkinter.TOP)
        notebook.grid_columnconfigure(0, weight=1)
        notebook.grid_columnconfigure(1, weight=1)

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

        db_save_button = ttk.Button(f_login, text="Save", command=saveDbLogins)
        db_save_button.grid(row=4, column=1, padx=10, pady=10, sticky='nsew')

        search_path_label = ttk.Label(f_settings, text="Library Search Path:")
        search_path_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        search_path_entry = ttk.Entry(f_settings)
        search_path_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='nsew')
        search_path_browse_button = ttk.Button(f_settings, text="Browse", command=browseBtn)
        search_path_browse_button.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')

        # Home page widgets
        f_componentEditor = ttk.LabelFrame(f_home, text="Component Editor", name="f_cc")
        f_componentEditor.grid(row=0, column=0, padx=10, pady=10, columnspan=1, sticky='nsw')
        f_tableView = ttk.LabelFrame(f_home, text="Table View", name="f_tableView")
        f_tableView.grid(row=1, column=0, padx=10, pady=(0, 10), rowspan=5, columnspan=5, sticky='nsew')
        for i in range(5):
            f_home.grid_columnconfigure(i, weight=1)
            f_home.grid_rowconfigure(i, weight=1)
            f_tableView.grid_columnconfigure(i, weight=1)
            f_tableView.grid_rowconfigure(i, weight=1)

        table_label = ttk.Label(f_componentEditor, text="DB Table:")
        table_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        table_cbox = ttk.Combobox(f_componentEditor, width=25, state="readonly")
        table_cbox.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        table_cbox.bind("<<ComboboxSelected>>", loadGUI)

        getDbLogins()
        testDbConnection()

        db_button = ttk.Button(f_componentEditor, text="Add new entry",
                               style=TKMT.ThemeStyles.ButtonStyles.AccentButton, command=addToDatabaseBtn)
        db_button.grid(row=7, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')
        db_button["state"] = "disabled"

        name_label = ttk.Label(f_componentEditor, text="Name:")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        name_entry = ttk.Entry(f_componentEditor, name="name", validate="all", validatecommand=(valNameCmd, '%P'))
        name_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='nsew')

        supplier_label = ttk.Label(f_componentEditor, text="Supplier 1:")
        supplier_label.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')
        supplier_cbox = ttk.Combobox(f_componentEditor, state="readonly", name="supplier 1")
        supplier_cbox.grid(row=1, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox['values'] = "Digi-Key"
        supplier_cbox.current(0)

        supplier_pn_label = ttk.Label(f_componentEditor, text="Supplier Part Number 1:")
        supplier_pn_label.grid(row=2, column=3, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry = ttk.Entry(f_componentEditor, name="supplier part number 1")
        supplier_pn_entry.grid(row=2, column=4, padx=(10, 0), pady=10, sticky='nsew')
        supplier_pn_entry.bind("<Return>", query_supplier_event)

        supplier_button = ttk.Button(f_componentEditor, image=ph_download, command=query_supplier)
        supplier_button.grid(row=2, column=5, padx=(10, 10), pady=10, ipady=0, sticky='nsew')

        search_path_label = ttk.Label(f_componentEditor, text="Library Path" + ":")
        search_path_label.grid(row=3, column=3, padx=10, pady=10, sticky='nsew')
        library_path_cbox = ttk.Combobox(f_componentEditor, name="library path",
                                         validate="all", validatecommand=(updateLibraryRefCmd, '%P'))
        library_path_cbox.grid(row=3, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')

        library_ref_label = ttk.Label(f_componentEditor, text="Library Ref" + ":")
        library_ref_label.grid(row=4, column=3, padx=10, pady=10, sticky='nsew')
        library_ref_cbox = ttk.Combobox(f_componentEditor, name="library ref")
        library_ref_cbox.grid(row=4, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')

        footprint_path_label = ttk.Label(f_componentEditor, text="Footprint Path" + ":")
        footprint_path_label.grid(row=5, column=3, padx=10, pady=10, sticky='nsew')
        footprint_path_cbox = ttk.Combobox(f_componentEditor, name="footprint path",
                                           validate="all", validatecommand=(updateFootprintRefCmd, '%P'))
        footprint_path_cbox.grid(row=5, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')

        footprint_ref_label = ttk.Label(f_componentEditor, text="Footprint Ref" + ":")
        footprint_ref_label.grid(row=6, column=3, padx=10, pady=10, sticky='nsew')
        footprint_ref_cbox = ttk.Combobox(f_componentEditor, name="footprint ref")
        footprint_ref_cbox.grid(row=6, column=4, columnspan=2, padx=10, pady=10, sticky='nsew')

        getLibSearchPath()
        self.run()

    libraryPathCurrentVal = ""
    footprintPathCurrentVal = ""


if __name__ == "__main__":
    App(str("sun-valley"), str("dark"))
