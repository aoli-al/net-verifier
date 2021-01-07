from pybatfish.client.commands import *
from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.flow import PathConstraints
from typing import List, Set
from pathlib import Path


class ConfigurationSimplifier(object):
    def __init__(self, snapshot: Path):
        bf_init_snapshot(str(snapshot), "origin", overwrite=True)
        load_questions()
        self.nodes = []
        results = bfq.nodeProperties().answer().frame()
        for _, result in results.iterrows():
            self.nodes.append(result.Node)

    def unreachable_switches(self, switches: List[str]) -> Set[str]:
        pending_nodes = set(self.nodes)
        pending_nodes.difference_update(switches)
        for switch in switches:
            reserved = set()
            for pending_node in pending_nodes:
                results = bfq.reachability(
                    pathConstraints=PathConstraints(startLocation=switch, endLocation=pending_node)).answer()
                results = results.frame()
                if results.size == 0:
                    continue
                reserved.add(pending_node)
                for _, result in results.iterrows():
                    for trace in result.Traces:
                        for hop in trace.hops:
                            reserved.add(hop.node)
            if 'as1border1' in reserved:
                print("?")
            pending_nodes.difference_update(reserved)
        return pending_nodes


# s = ConfigurationSimplifier("/home/leo/repos/verifier/configs/test")
# print(s.unreachable_switches(["as2dept1"]))
