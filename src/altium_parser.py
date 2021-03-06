import os.path
import re
import io


def getLibraryRefList(filepath):
    _, fileExtension = os.path.splitext(filepath)
    if fileExtension == '.SchLib':
        try:
            f = io.open(filepath, mode="r", encoding="latin-1")
            result = re.findall('LibReference=(.*?)[|]', f.read())
        except PermissionError:
            result = []
        except FileNotFoundError:
            result = []

        print(f"Parsing {filepath} for symbols: {len(result)} components found")
        return result
    return []


def getFootprintRefList(filepath):
    _, fileExtension = os.path.splitext(filepath)
    if fileExtension == '.PcbLib':
        try:
            f = io.open(filepath, mode="r", encoding="latin-1")
            result = re.findall('PATTERN=(.*?)[|]', f.read())
        except PermissionError:
            result = []
        except FileNotFoundError:
            result = []

        print(f"Parsing {filepath} for footprints: {len(result)} components found")
        return result
    return []
