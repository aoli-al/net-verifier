import json
import sys


f = json.load(open("out-policy-map.json"))
print(len(set(f.keys())))
