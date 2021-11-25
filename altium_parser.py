import re
import io


def getLibraryRefList(filepath):
    try:
        f = io.open(filepath, mode="r", encoding="latin-1")
        result = re.findall('LibReference=(.*?)[|]', f.read())
    except PermissionError:
        result = []
    except FileNotFoundError:
        result = []

    print(f"Parsing {filepath} for symbols: {len(result)} components found")
    return result


def getFootprintRefList(filepath):
    try:
        f = io.open(filepath, mode="r", encoding="latin-1")
        result = re.findall('PATTERN=(.*?)[|]', f.read())
    except PermissionError:
        result = []
    except FileNotFoundError:
        result = []

    print(f"Parsing {filepath} for footprints: {len(result)} components found")
    return result
