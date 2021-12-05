import os
import digikey

os.environ['DIGIKEY_CLIENT_ID'] = 'il5UCEPjQRedAgJ6ssO3VJrL3dU65gh0'
os.environ['DIGIKEY_CLIENT_SECRET'] = 'kcXe6QYpoFQmfZUZ'
os.environ['DIGIKEY_CLIENT_SANDBOX'] = 'False'
os.environ['DIGIKEY_STORAGE_PATH'] = os.getenv('APPDATA') + '\\Altium DB GUI\\json'


# Query product number
def fetchDigikeyData(digikeyPartNumber, requestedParams, paramDict):
    try:
        part = digikey.product_details(digikeyPartNumber)
        result = []
        dkDataDict = {}
        paramDict = dict((v, k) for k, v in paramDict.items())

        for p in part.parameters:
            p_dict = p.to_dict()
            param, value = p_dict['parameter'], p_dict['value']
            if param in paramDict:
                dkDataDict[paramDict[param]] = value

        for column in requestedParams:
            if column == "Description":
                value = part.detailed_description
            elif column == "Manufacturer Part Number":
                value = part.manufacturer_part_number
            elif column == "Manufacturer":
                value = part.manufacturer.to_dict()['value']
            elif column == "Unit Price":
                value = part.standard_pricing[0].to_dict()['unit_price']
            else:
                try:
                    value = dkDataDict[column]
                except KeyError:
                    value = ""
                    print(f"No match found for \'{column}\'")
            result.append([column, value])
        return result
    except AttributeError:
        print("Digi-Key Supplier Part Number API Request Failed")
    return []


def fetchDigikeySupplierPN(manufacturerPartNumber):
    supplierPN = ""
    try:
        part = digikey.product_details(manufacturerPartNumber)
        supplierPN = part.digi_key_part_number
    except AttributeError:
        print("Digi-Key Manufacturer Part Number API Request Failed")
    return supplierPN
