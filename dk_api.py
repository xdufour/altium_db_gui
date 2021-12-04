import os
import digikey

os.environ['DIGIKEY_CLIENT_ID'] = 'il5UCEPjQRedAgJ6ssO3VJrL3dU65gh0'
os.environ['DIGIKEY_CLIENT_SECRET'] = 'kcXe6QYpoFQmfZUZ'
os.environ['DIGIKEY_CLIENT_SANDBOX'] = 'False'
os.environ['DIGIKEY_STORAGE_PATH'] = 'C:/cache_dir'

capacitor_dict = {
    "Capacitance": "Capacitance",
    "Tolerance": "Tolerance",
    "Voltage - Rated": "Voltage Rating",
}

opamp_dict = {
    "Number of Circuits": "Nb Of Circuits",
    "Slew Rate": "Slew Rate",
    "Voltage - Span (Max)": "Voltage Supply",
}

resistor_dict = {
    "Resistance": "Resistance",
    "Tolerance": "Tolerance",
    "Power (Watts)": "Power",
    "Temperature Coefficient": "Temperature Coefficient"
}

dictionary_map = {
    "capacitors": capacitor_dict,
    "opamps": opamp_dict,
    "resistors": resistor_dict
}


# Query product number
def fetchDigikeyData(dkpn, tableName, dbColumnList):
    try:
        part = digikey.product_details(dkpn)
        result = []
        dk_data = {}
        param_dict = dictionary_map[tableName]

        for p in part.parameters:
            p_dict = p.to_dict()
            param, value = p_dict['parameter'], p_dict['value']
            if param in param_dict:
                dk_data[param_dict[param]] = value

        for column in dbColumnList:
            if column == "Description":
                value = part.detailed_description
            elif column == "Manufacturer Part Number":
                value = part.manufacturer_part_number
            elif column == "Manufacturer":
                value = part.manufacturer.to_dict()['value']
            else:
                try:
                    value = dk_data[column]
                except KeyError:
                    value = ""
                    print(f"No match found for \'{column}\'")
            result.append([column, value])
        return result
    except AttributeError:
        print("Digi-Key API Request Failed: No Results")
    return []

