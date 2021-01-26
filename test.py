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

# process_json("configs/multihosts")
# convert_csv("configs/multihosts/raw.csv")
# merge_two_files("out-complete-list-affected-nodes.json", "out-2-random-selected-nodes.json")
# bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/multihosts", "multihosts")
# build_reachability("/home/leo/repos/sdn-verifier/configs/Working_Enterprise")
# print(check_invalid_policies("configs/complete-issue/policies.csv", "configs/complete-issue"))
# sys.exit(0)

# load_questions()
# generate_hosts("/home/leo/repos/sdn-verifier/configs/multihosts")
# remove_links("/home/leo/repos/sdn-verifier/configs/multihosts")

# bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/default", "t1")
# bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/example", "example")
# bf_init_snapshot("/home/leo/repos/sdn-verifier/configs/alternate-routes", "t2")


# v = VerifyInvariant("/home/leo/repos/sdn-verifier/configs/Working_Enterprise")
# v.run()
v = Harness("/home/leo/repos/sdn-verifier/configs/Working_Enterprise")
v.run()
v = VerifyInvariant("/home/leo/repos/sdn-verifier/configs/multihosts")
v.run()



# result = {}

# for i in range(1, 42):
#     result[i] = {}
#     for j in range(1, 42):
#         if i != j:
#             results = bfq.reachability(
#                 pathConstraints=PathConstraints(startLocation=f"host{i}", endLocation=f"host{j}")) \
#                 .answer(snapshot="multihosts").frame()
#             if results.size > 0:
#                 print(f"host{i} host{j} True")
#                 result[i][j] = True
#             else:
#                 print(f"host{i} host{j} False")
#                 result[i][j] = False

# json.dump(result, open("matrix.json", "w"), indent=2)


# results = bfq.reachability(headers=HeaderConstraints(srcIps="host1", dstIps="host2")) \
#     .answer(snapshot="multihosts").frame()
# for idx, result in results.iterrows():
#     print(result.Flow)

def convert_list_to_tuple(obj):
    if isinstance(obj, list):
        result = []
        for o in obj:
            result.append(convert_list_to_tuple(o))
        return tuple(result)
    if hasattr(obj, "__dict__"):
        t = type(obj)
        values = obj.__dict__
        for key, value in values.items():
            values[key] = convert_list_to_tuple(value)
        return values
        # new_obj = type(t.__name__, t.__bases__, values)
        # return new_obj
    return obj


# nodes = []
# results = bfq.nodeProperties().answer(snapshot="t1").frame()
# for _, result in results.iterrows():
#     nodes.append(result.Node)


def get_traces(nodes: List[str], snapshot: str):
    traces = {}
    for n1 in nodes:
        for n2 in nodes:
            results = bfq.traceroute(startLocation=n1,
                                     headers=HeaderConstraints(dstIps=n2)).answer(snapshot=snapshot).frame()
            for idx, result in results.iterrows():
                for trace in result.Traces:
                    if trace.disposition not in traces:
                        traces[trace.disposition] = set()
                    hops_str = json.dumps(convert_list_to_tuple(trace.hops))
                    traces[trace.disposition].add(hops_str)
    return traces


# traces1 = get_traces(nodes, "t1")
# traces2 = get_traces(nodes, "t2")
# for key in traces1:
#     set1 = traces1[key]
#     set2 = traces2[key]
#     result = (set1 - set2).union(set2 - set1)
#     print(result)

# h = Harness("/home/leo/repos/sdn-verifier/configs/Working_Enterprise")
# h.run()


# print(Commands([NodeCommand("/as1.*/", "", {"aaa"}),
#                 NodeCommand("/as.core./", "", {"bbb"})]).compute())
# print(interfaces_from_snapshot("example"))
# print(len(interfaces_from_snapshot("example")))
# print(build_policies_from_csv("/home/leo/tmp/policies.csv"))
#
# n = CrystalNet("t1", ["as2core1"])
# print(n.get_affected_interfaces())
#
# n = Heimdall("t1", ["as2core1"])
# print(n.get_affected_interfaces())
# Waypoint()
# wp = Waypoint("as3border2", "3.1.1.1/32", "as3core1")
# print(wp.eval("", "t1"))
# result = bfq.layer3Edges().answer().frame()
# print(result)
# results = bfq.compareFilters().answer(snapshot="t2", reference_snapshot="t1").frame()
# results = bfq.nodeProperties(nodes="/.*/").answer().frame()

# results = bfq.traceroute(startLocation='as2dept1', headers=HeaderConstraints()).answer(snapshot="t2").frame()
# results = bfq.differentialReachability(
# ).answer(snapshot="t1", reference_snapshot="t2").frame()
# print(results.size)

# for idx, result in results.iterrows():
#     print(result.Node)
    # for trace in result.Traces:
    #     print(trace)
