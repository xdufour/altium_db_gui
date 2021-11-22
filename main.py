import tkinter
import TKinterModernThemes as TKMT
from tkinter import ttk
import dk_api
import mysql_query
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
        cnx = mysql_query.init()
        dbColumnNames = []

        img_home = Image.open('home.png')
        img_home.thumbnail(size=(32, 32))
        ph_home = ImageTk.PhotoImage(img_home)
        img_settings = Image.open('settings.png')
        img_settings.thumbnail(size=(32, 32))
        ph_settings = ImageTk.PhotoImage(img_settings)

        def loadGui(event):
            dbColumnList = mysql_query.getTableColumns(cnx, table_cbox.get().lower())
            row = 2
            # Delete any previously created widgets
            for column in dbColumnNames:
                if column not in permanentParams:
                    self.root.nametowidget(".nbk.f1." + column.lower()).destroy()
                    self.root.nametowidget(".nbk.f1." + column.lower() + "_l").destroy()
            dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnList):
                dbColumnNames.append(column[0])
                if dbColumnNames[i] not in permanentParams:
                    label = ttk.Label(f1, text=dbColumnNames[i] + ":", name=(dbColumnNames[i].lower() + "_l"))
                    label.grid(row=row, column=0, padx=10, pady=10, sticky='nsew')
                    entry = ttk.Entry(f1, name=dbColumnNames[i].lower())
                    entry.grid(row=row, column=1, padx=10, pady=10, sticky='nsew')
                    row = row + 1
            print(f"Reloaded GUI for {table_cbox.get()}")

        def query_supplier_event(event):
            query_supplier()

        def query_supplier():
            dkpn = supplier_pn_entry.get()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, table_cbox.get(), strippedList(dbColumnNames, permanentParams))
            print(result)
            for it in result:
                try:
                    self.root.nametowidget(".nbk.f1." + it[0].lower()).delete(0, 255)
                    self.root.nametowidget(".nbk.f1." + it[0].lower()).insert(0, it[1])
                except KeyError:
                    print(f"No widget named {it[0].lower()}")

        def addToDatabaseBtn():
            rowData = []
            for col in dbColumnNames:
                try:
                    rowData.append(self.root.nametowidget(".nbk.f1." + col.lower()).get())
                except KeyError:
                    print(f"No widget named {col.lower()}")
            mysql_query.insertInDatabase(cnx, table_cbox.get().lower(), dbColumnNames, rowData)

        def validateName(input):
            if len(input) > 0:
                db_button["state"] = "normal"
            else:
                db_button["state"] = "disabled"
            return True
        valNameCmd = self.root.register(validateName)

        style = ttk.Style(self.master)
        style.configure('lefttab.TNotebook', tabposition='wn', tabmargins=[-10, -5, -16, 0])
        style.configure('lefttab.TNotebook.Tab', padding=[0, 0])

        notebook = ttk.Notebook(self.master, style='lefttab.TNotebook', name="nbk")
        notebook.grid(row=0, column=0, rowspan=5, columnspan=5, padx=0, pady=0, sticky='nsew')
        f1 = ttk.Frame(notebook, name="f1")
        f2 = ttk.Frame(notebook, name="f2")
        f1.pack(fill='both', expand=True)
        f2.pack(fill='both', expand=True)

        notebook.add(f1, image=ph_home, compound=tkinter.TOP)
        notebook.add(f2, image=ph_settings, compound=tkinter.TOP)

        table_label = ttk.Label(f1, text="DB Table:")
        table_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        table_cbox = ttk.Combobox(f1, state="readonly")
        table_cbox.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        table_cbox['values'] = getDbTableList(cnx)

        table_cbox.bind("<<ComboboxSelected>>", loadGui)
        table_cbox.current(0)

        db_button = ttk.Button(f1, text="Add to database", command=addToDatabaseBtn)
        db_button.grid(row=0, column=3, padx=10, pady=10, sticky='nsew')
        db_button["state"] = "disabled"

        name_label = ttk.Label(f1, text="Name:")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        name_entry = ttk.Entry(f1, name="name", validate="all", validatecommand=(valNameCmd, '%P'))
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        supplier_label = ttk.Label(f1, text="Supplier 1:")
        supplier_label.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox = ttk.Combobox(f1, state="readonly", name="supplier 1")
        supplier_cbox.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')
        supplier_cbox['values'] = "Digi-Key"
        supplier_cbox.current(0)

        supplier_pn_label = ttk.Label(f1, text="Supplier Part Number 1:")
        supplier_pn_label.grid(row=2, column=2, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry = ttk.Entry(f1, name="supplier part number 1")
        supplier_pn_entry.grid(row=2, column=3, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry.bind("<Return>", query_supplier_event)

        supplier_button = ttk.Button(f1, text="Autofill", command=query_supplier)
        supplier_button.grid(row=2, column=4, padx=10, pady=10, sticky='nsew')

        library_path_label = ttk.Label(f1, text="Library Path" + ":")
        library_path_label.grid(row=3, column=2, padx=10, pady=10, sticky='nsew')
        library_path_entry = ttk.Entry(f1, name="library path")
        library_path_entry.grid(row=3, column=3, padx=10, pady=10, sticky='nsew')

        library_ref_label = ttk.Label(f1, text="Library Ref" + ":")
        library_ref_label.grid(row=4, column=2, padx=10, pady=10, sticky='nsew')
        library_ref_entry = ttk.Entry(f1, name="library ref")
        library_ref_entry.grid(row=4, column=3, padx=10, pady=10, sticky='nsew')

        footprint_path_label = ttk.Label(f1, text="Footprint Path" + ":")
        footprint_path_label.grid(row=5, column=2, padx=10, pady=10, sticky='nsew')
        footprint_path_entry = ttk.Entry(f1, name="footprint path")
        footprint_path_entry.grid(row=5, column=3, padx=10, pady=10, sticky='nsew')

        footprint_ref_label = ttk.Label(f1, text="Footprint Ref" + ":")
        footprint_ref_label.grid(row=6, column=2, padx=10, pady=10, sticky='nsew')
        footprint_ref_entry = ttk.Entry(f1, name="footprint ref")
        footprint_ref_entry.grid(row=6, column=3, padx=10, pady=10, sticky='nsew')

        loadGui(0)
        self.run()


if __name__ == "__main__":
    App(str("sun-valley"), str("dark"))
