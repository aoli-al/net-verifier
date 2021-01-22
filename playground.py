import json
import sys
from pybatfish.question import bfq
from pybatfish.datamodel import HeaderConstraints, PathConstraints, Hop
from pybatfish.question.question import load_questions
from pybatfish.client.commands import bf_init_snapshot, bf_set_network
from typing import List
import json
from command import *
from policy import *
from experiment import *
from utils import *
import json
import sys


load_questions()

bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/multihosts", "multihosts")
interfaces = list(interfaces_from_snapshot("multihosts"))
idx = 0
visited = set()
for i in range(len(interfaces)):
    i1 = interfaces[i]
    if "host" in i1:
        continue
    visited.add(i1)
    for j in range(i, len(interfaces)):
        i2 = interfaces[j]
        if "host" in i2:
            continue
        if i1 == i2:
            continue
        if f"{i1},{i2}" not in visited and f"{i2},{i1}" not in visited:
            visited.add(f"{i1},{i2}")

print(len(visited))

f = json.load(open("out-policy-map.json"))
print(len(set(f.keys())))


s = set()
for key in f.keys():
    s.add(",".join(sorted(key.split(","))))
print(len(s))
