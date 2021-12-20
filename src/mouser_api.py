import os
import csv
import json
import requests
import utils
from bs4 import BeautifulSoup

# Mouser Base URL
BASE_URL = 'https://api.mouser.com/api/v1.0'
os.environ['MOUSER_PART_API_KEY'] = '985e159d-3352-4bf8-a066-6dcf2cd58ad6'

userAgentList = [
    "Mozilla/5.0",
    "Chrome/96.0.4664.110",
    "Safari/537.36"
]


def get_api_keys(filename=None):
    """ Mouser API Keys """

    # Look for API keys in environmental variables
    api_keys = [
        os.environ.get('MOUSER_ORDER_API_KEY', ''),
        os.environ.get('MOUSER_PART_API_KEY', ''),
    ]
    return api_keys


class MouserAPIRequest:
    """ Mouser API Request """

    url = None
    api_url = None
    method = None
    body = {}
    response = None
    api_key = None

    def __init__(self, url, method, file_keys=None, *args):
        if not url or not method:
            return None
        self.api_url = BASE_URL + url
        self.method = method

        # Append argument
        if len(args) == 1:
            self.api_url += '/' + str(args[0])

        # Append API Key
        if self.name == 'Part Search':
            self.api_key = get_api_keys(file_keys)[1]
        else:
            self.api_key = get_api_keys(file_keys)[0]

        if self.api_key:
            self.url = self.api_url + '?apiKey=' + self.api_key

    def get(self, url):
        response = requests.get(url=url)
        return response

    def post(self, url, body):
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(url=url, data=json.dumps(body), headers=headers)
        return response

    def run(self, body={}):
        if self.method == 'GET':
            self.response = self.get(self.url)
        elif self.method == 'POST':
            self.response = self.post(self.url, body)

        return True if self.response else False

    def get_response(self):
        if self.response is not None:
            try:
                return json.loads(self.response.text)
            except json.decoder.JSONDecodeError:
                return self.response.text

        return {}

    def print_response(self):
        print(json.dumps(self.get_response(), indent=4, sort_keys=True))


class MouserBaseRequest(MouserAPIRequest):
    """ Mouser Base Request """

    name = ''
    allowed_methods = ['GET', 'POST']
    operation = None
    operations = {}

    def __init__(self, operation, file_keys=None, *args):
        ''' Init '''

        if operation not in self.operations:
            print(f'[{self.name}]\tInvalid Operation')
            print('-' * 10)

            valid_operations = [operation for operation, values in self.operations.items() if values[0] and values[1]]
            if valid_operations:
                print('Valid operations:')
                for operation in valid_operations:
                    print(f'- {operation}')
            return

        self.operation = operation
        (method, url) = self.operations.get(self.operation, ('', ''))

        if not url or not method or method not in self.allowed_methods:
            print(f'[{self.name}]\tOperation "{operation}" Not Yet Supported')
            return

        super().__init__(url, method, file_keys, *args)

    def export_csv(self, file_path: str, data: dict):
        ''' Export dictionary data to CSV '''

        with open(file_path, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)

            for row in data:
                csvwriter.writerow(row)


class MouserPartSearchRequest(MouserBaseRequest):
    """ Mouser Part Search Request """

    name = 'Part Search'
    operations = {
        'keyword': ('', ''),
        'keywordandmanufacturer': ('', ''),
        'partnumber': ('POST', '/search/partnumber'),
        'partnumberandmanufacturer': ('', ''),
        'manufacturerlist': ('', ''),
    }

    def get_clean_response(self):
        cleaned_data = {
            'Availability': '',
            'Category': '',
            'DataSheetUrl': '',
            'Description': '',
            'ImagePath': '',
            'Manufacturer': '',
            'ManufacturerPartNumber': '',
            'MouserPartNumber': '',
            'ProductDetailUrl': '',
            'ProductAttributes': [],
            'PriceBreaks': [],
        }

        response = self.get_response()
        if self.get_response():
            try:
                parts = response['SearchResults'].get('Parts', [])
            except AttributeError:
                parts = None

            if parts:
                # Process first part
                part_data = parts[0]
                # Merge
                for key in cleaned_data:
                    cleaned_data[key] = part_data.get(key, '')

        return cleaned_data

    def print_clean_response(self):
        response_data = self.get_clean_response()
        print(json.dumps(response_data, indent=4, sort_keys=True))

    def get_body(self, **kwargs):

        body = {}

        if self.operation == 'partnumber':
            part_number = kwargs.get('part_number', None)
            option = kwargs.get('option', 'None')

            if part_number:
                body = {
                    'SearchByPartRequest': {
                        'mouserPartNumber': part_number,
                        'partSearchOptions': option,
                    }
                }

        return body

    def part_search(self, part_number, option='None'):
        '''Mouser Part Number Search '''

        kwargs = {
            'part_number': part_number,
            'option': option,
        }

        self.body = self.get_body(**kwargs)

        if self.api_key:
            return self.run(self.body)
        else:
            return False


def fetchMouserSupplierPN(manufacturerPartNumber):
    mouserRequest = MouserPartSearchRequest('partnumber')
    mouserRequest.part_search(manufacturerPartNumber)
    res = mouserRequest.get_clean_response()
    supplierPN = ""
    try:
        supplierPN = res['MouserPartNumber']
        print(f"Mouser Part Number: {supplierPN}")
    except KeyError:
        print(f"No Mouser Part Number found for {manufacturerPartNumber}")
    return supplierPN


def fetchMouserData(mouserPartNumber, requestedParams, paramDict):
    url = f"https://www.mouser.ca/c/?q={mouserPartNumber}"

    result = []
    paramList = []
    valueList = []
    scrapedDict = {}
    mouserDataDict = {}
    requestSuccess = False

    for u in userAgentList:
        requestHeader = {'User-Agent': u}
        r = requests.get(url, headers=requestHeader)
        if r.status_code == 200:
            requestSuccess = True
            print(u)
            break

    if not requestSuccess:
        print("Mouser Web Scraping Failed: Access Forbidden")
        return []

    try:
        soup = BeautifulSoup(r.text, 'lxml')
        table = soup.find("table", {"class": "table persist-area SearchResultsTable"})
        if table is not None:  # Mouser found multiple entries, parse search results and use 1st row
            header = table.find("tr", {"class": "headerRow persist-header"})
            body = table.find("tbody")
            row = body.find("tr", recursive=False)
            params = header.find_all("th")
            values = row.find_all("td", recursive=False)
            scrapedDict['Manufacturer'] = row.attrs.get('data-actualmfrname')
            scrapedDict['Manufacturer Part Number'] = row.attrs.get('data-mfrpartnumber')
            for p in params:
                paramList.append(utils.strReplaceMultiple(p.text.strip(), ['\n', '\r'], ''))
            for v in values:
                valueList.append(utils.strReplaceMultiple(v.text.strip(), ['\n', '\r'], ''))
        else:  # Mouser found unique match, parse component specs table
            table = soup.find("table", {"class": "specs-table"})
            rows = table.find_all("tr")
            desc = soup.find("span", {"id": "spnDescription"})
            mfg = soup.find("a", {"id": "lnkManufacturerName"})
            mfgPn = soup.find("span", {"id": "spnManufacturerPartNumber"})
            if desc is not None:
                scrapedDict['Description'] = desc.text.strip()
            if mfg is not None:
                scrapedDict['Manufacturer'] = mfg.text.strip()
            if mfgPn is not None:
                scrapedDict['Manufacturer Part Number'] = mfgPn.text.strip()
            for r in rows:
                p = r.find("td", {"class": "attr-col"})
                v = r.find("td", {"class": "attr-value-col"})
                if p is not None and v is not None:
                    paramList.append(utils.strReplaceMultiple(p.text.strip(), ['\n', '\r', ':'], ''))
                    valueList.append(utils.strReplaceMultiple(v.text.strip(), ['\n', '\r'], ''))

        for i, pText in enumerate(paramList):
            scrapedDict[pText] = valueList[i]

        paramDict = dict((v, k) for k, v in paramDict.items())

        for param in scrapedDict:
            value = scrapedDict[param]
            if param in paramDict:
                mouserDataDict[paramDict[param]] = value

        for column in requestedParams:
            if column == "Description":
                value = scrapedDict.get(column).replace('Learn More', '')
            elif column == "Manufacturer Part Number":
                value = scrapedDict.get(column)
            elif column == "Manufacturer":
                value = scrapedDict.get(column)
            elif column == "Unit Price":
                value = 'N/A'
            else:
                value = mouserDataDict.get(column, "")
            result.append([column, value])

        return result
    except AttributeError:
        print("Mouser Web Scraping Failed: Invalid Part Number")
    return []




