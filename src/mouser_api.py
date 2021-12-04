import os
import csv
import json
import requests

# Mouser Base URL
BASE_URL = 'https://api.mouser.com/api/v1.0'
os.environ['MOUSER_PART_API_KEY'] = '985e159d-3352-4bf8-a066-6dcf2cd58ad6'


def get_api_keys(filename=None):
    """ Mouser API Keys """

    # Look for API keys in environmental variables
    api_keys = [
        os.environ.get('MOUSER_ORDER_API_KEY', ''),
        os.environ.get('MOUSER_PART_API_KEY', ''),
    ]

    # Else look into configuration file
    if not (api_keys[0] or api_keys[1]) and filename:
        try:
            with open(filename, 'r') as keys_in_file:
                api_keys = []

                for key in keys_in_file:
                    api_keys.append(key.replace('\n', ''))

                if len(api_keys) == 2:
                    return api_keys
                else:
                    pass
        except FileNotFoundError:
            print(f'[ERROR]\tAPI Keys File "{filename}" Not Found')

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


class MouserCartRequest(MouserBaseRequest):
    """ Mouser Cart Request """

    name = 'Cart'
    operations = {
        'get': ('', ''),
        'update': ('', ''),
        'insertitem': ('', ''),
        'updateitem': ('', ''),
        'removeitem': ('', ''),
    }


class MouserOrderHistoryRequest(MouserBaseRequest):
    """ Mouser Order History Request """

    name = 'Order History'
    operations = {
        'ByDateFilter': ('', ''),
        'ByDateRange': ('', ''),
    }


class MouserOrderRequest(MouserBaseRequest):
    """ Mouser Order Request """

    name = 'Order'
    operations = {
        'get': ('GET', '/order'),
        'create': ('', ''),
        'submit': ('', ''),
        'options': ('', ''),
        'currencies': ('', ''),
        'countries': ('', ''),
    }

    def export_order_lines_to_csv(self, order_number='', clean=False):
        ''' Export Order Lines to CSV '''

        def convert_order_lines_to_list(clean=False):

            if clean:
                # Exclude following columns
                exclude_col = [
                    'Errors',
                    'MouserATS',
                    'PartsPerReel',
                    'ScheduledReleases',
                    'InfoMessages',
                    'CartItemCustPartNumber',
                    'LifeCycle',
                    'SalesMultipleQty',
                    'SalesMinimumOrderQty',
                    'SalesMaximumOrderQty',
                ]
            else:
                exclude_col = []

            response_data = self.get_response()
            data_list = []
            if 'OrderLines' in response_data:
                order_lines = response_data['OrderLines']

                headers = [key for key in order_lines[0] if key not in exclude_col]
                data_list.append(headers)

                for order_line in order_lines:
                    line = [value for key, value in order_line.items() if key not in exclude_col]
                    data_list.append(line)

                return data_list

        data_to_export = convert_order_lines_to_list(clean)
        filename = '_'.join([self.name, order_number]) + '.csv'
        # Export to CSV file
        self.export_csv(filename, data_to_export)

        return filename


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
                    cleaned_data[key] = part_data[key]

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


def fetchSupplierPN(manufacturerPartNumber):
    mouserRequest = MouserPartSearchRequest('partnumber')
    mouserRequest.part_search(manufacturerPartNumber)
    res = mouserRequest.get_clean_response()
    supplierPN = ""
    try:
        supplierPN = res['MouserPartNumber']
    except KeyError:
        print(f"No Mouser Part Number found for {manufacturerPartNumber}")
    return supplierPN