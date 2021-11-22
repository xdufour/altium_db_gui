import TKinterModernThemes as TKMT
from tkinter import ttk
import dk_api
import mysql_query

permanentWidgets = ["Name", "Supplier 1", "Supplier Part Number 1", "Library Path",
                    "Library Ref", "Footprint Path", "Footprint Ref"]


class App(TKMT.ThemedTKinterFrame):
    def __init__(self, theme, mode, usecommandlineargs=False, usethemeconfigfile=False):
        super().__init__(str("Altium DB GUI"), theme, mode, usecommandlineargs, usethemeconfigfile)
        cnx = mysql_query.init()
        dbColumnNames = []

        def loadGui(event):
            dbColumnList = mysql_query.getDatabaseColumns(cnx, table_cbox.get().lower())
            row = 2
            # Delete any previously created widgets
            for column in dbColumnNames:
                if column not in permanentWidgets:
                    self.root.nametowidget(column.lower()).destroy()
                    self.root.nametowidget(column.lower() + "_l").destroy()
            dbColumnNames.clear()
            # Create widgets
            for i, column in enumerate(dbColumnList):
                dbColumnNames.append(column[0])
                if dbColumnNames[i] not in permanentWidgets:
                    label = ttk.Label(self.master, text=dbColumnNames[i] + ":", name=(dbColumnNames[i].lower() + "_l"))
                    label.grid(row=row, column=0, padx=10, pady=10, sticky='nsew')
                    entry = ttk.Entry(self.master, name=dbColumnNames[i].lower())
                    entry.grid(row=row, column=1, padx=10, pady=10, sticky='nsew')
                    row = row + 1
            print(f"Reloaded GUI for {table_cbox.get()}")

        def query_supplier_event(event):
            query_supplier()

        def query_supplier():
            dkpn = supplier_pn_entry.get()
            print(f"Querying Digi-Key for {dkpn}")
            result = dk_api.fetchDigikeyData(dkpn, table_cbox.get().lower(), dbColumnNames)
            print(result)
            for it in result:
                if it[0] not in ["Supplier 1", "Supplier Part Number 1"]:
                    try:
                        self.root.nametowidget(it[0].lower()).delete(0, 255)
                        self.root.nametowidget(it[0].lower()).insert(0, it[1])
                    except KeyError:
                        print(f"No widget named {it[0].lower()}")

        def addToDatabaseBtn():
            rowData = []
            for col in dbColumnNames:
                try:
                    rowData.append(self.root.nametowidget(col.lower()).get())
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

        table_label = ttk.Label(self.master, text="DB Table:")
        table_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        table_cbox = ttk.Combobox(self.master, state="readonly")
        table_cbox.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        table_cbox['values'] = ("Capacitors", "OpAmps")

        table_cbox.bind("<<ComboboxSelected>>", loadGui)
        table_cbox.current(0)

        db_button = ttk.Button(self.master, text="Add to database", command=addToDatabaseBtn)
        db_button.grid(row=0, column=3, padx=10, pady=10, sticky='nsew')
        db_button["state"] = "disabled"

        name_label = ttk.Label(self.master, text="Name:")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        name_entry = ttk.Entry(self.master, name="name", validate="all", validatecommand=(valNameCmd, '%P'))
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        supplier_label = ttk.Label(self.master, text="Supplier 1:")
        supplier_label.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')
        supplier_cbox = ttk.Combobox(self.master, state="readonly", name="supplier 1")
        supplier_cbox.grid(row=1, column=3, padx=10, pady=10, sticky='nsew')
        supplier_cbox['values'] = "Digi-Key"
        supplier_cbox.current(0)

        supplier_pn_label = ttk.Label(self.master, text="Supplier Part Number 1:")
        supplier_pn_label.grid(row=2, column=2, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry = ttk.Entry(self.master, name="supplier part number 1")
        supplier_pn_entry.grid(row=2, column=3, padx=10, pady=10, sticky='nsew')
        supplier_pn_entry.bind("<Return>", query_supplier_event)

        supplier_button = ttk.Button(self.master, text="Autofill", command=query_supplier)
        supplier_button.grid(row=2, column=4, padx=10, pady=10, sticky='nsew')

        library_path_label = ttk.Label(self.master, text="Library Path" + ":")
        library_path_label.grid(row=3, column=2, padx=10, pady=10, sticky='nsew')
        library_path_entry = ttk.Entry(self.master, name="library path")
        library_path_entry.grid(row=3, column=3, padx=10, pady=10, sticky='nsew')

        library_ref_label = ttk.Label(self.master, text="Library Ref" + ":")
        library_ref_label.grid(row=4, column=2, padx=10, pady=10, sticky='nsew')
        library_ref_entry = ttk.Entry(self.master, name="library ref")
        library_ref_entry.grid(row=4, column=3, padx=10, pady=10, sticky='nsew')

        footprint_path_label = ttk.Label(self.master, text="Footprint Path" + ":")
        footprint_path_label.grid(row=5, column=2, padx=10, pady=10, sticky='nsew')
        footprint_path_entry = ttk.Entry(self.master, name="footprint path")
        footprint_path_entry.grid(row=5, column=3, padx=10, pady=10, sticky='nsew')

        footprint_ref_label = ttk.Label(self.master, text="Footprint Ref" + ":")
        footprint_ref_label.grid(row=6, column=2, padx=10, pady=10, sticky='nsew')
        footprint_ref_entry = ttk.Entry(self.master, name="footprint ref")
        footprint_ref_entry.grid(row=6, column=3, padx=10, pady=10, sticky='nsew')

        loadGui(0)
        self.run()


if __name__ == "__main__":
    App(str("sun-valley"), str("dark"))
