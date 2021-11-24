import re
import io

f = io.open("tinyFG.SchLib", mode="r", encoding="latin-1")

result = re.findall('LibReference=(.*?)[|]', f.read())

print("tinyFG.SchLib:")
for item in result:
    print(item)

print("PcbLib1.PcbLib:")
f = io.open("PcbLib1.PcbLib", mode="r", encoding="latin-1")

result = re.findall('PATTERN=(.*?)[|]', f.read())

for item in result:
    print(item)
