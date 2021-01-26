import json
import sys
from pybatfish.question import bfq
from pybatfish.datamodel import HeaderConstraints, PathConstraints, Hop
from pybatfish.question.question import load_questions
from pybatfish.client.commands import bf_init_snapshot, bf_set_network, bf_upload_diagnostics
from typing import List
import json
from command import *
from policy import *
from experiment import *
from utils import *
import json
import sys

load_questions()
compute_issue_reachable_nodes("configs/Working_Enterprise", "configs/issues/working-enterprise/ospf")
# compute_issue_reachable_nodes("configs/Working_Enterprise", "configs/working-enterprise/reconfiguration")
# compute_issue_reachable_nodes("configs/Working_Enterprise", "configs/working-enterprise/vlan")
# compute_issue_reachable_nodes("configs/multihosts", "configs/issues/multihosts/as2border1")
# compute_issue_reachable_nodes("configs/multihosts", "configs/issues/multihosts/multihosts")




# def batfish_client(path, snapshot):
#     return check_invalid_policies("", "")
#
# print(check_invalid_policies("configs/multihosts/policies.csv", "configs/multihosts"))
# sys.exit(0)
#
#
# bf_init_snapshot("/home/leo/tests/CompleteIssue", "reduced-links")
# # bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/reduced-links", "reduced-links")
# bf_upload_diagnostics(dry_run=True, contact_info='<optional email address>')
# b = bfq.reachability().answer().frame()
# print(b)


# process_json("reduced-links", "configs/reduced-links/raw.json")
# convert_csv("configs/reduced-links/raw.csv")
# interfaces = list(interfaces_from_snapshot("multihosts"))
# idx = 0
# visited = set()
# for i in range(len(interfaces)):
#     i1 = interfaces[i]
#     if "host" in i1:
#         continue
#     visited.add(i1)
#     for j in range(i, len(interfaces)):
#         i2 = interfaces[j]
#         if "host" in i2:
#             continue
#         if i1 == i2:
#             continue
#         if f"{i1},{i2}" not in visited and f"{i2},{i1}" not in visited:
#             visited.add(f"{i1},{i2}")
#
# print(len(visited))
#
# f = json.load(open("out-policy-map.json"))
# print(len(set(f.keys())))
#
#
# s = set()
# for key in f.keys():
#     s.add(",".join(sorted(key.split(","))))
# print(len(s))


s = '''
issue:
commands not necessary
interface commands and router commands

interface is down 
only interface command is allowed.

'''
