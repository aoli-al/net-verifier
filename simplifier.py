from pybatfish.client.commands import *
from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints
from typing import List

bf_session.host = 'localhost'
class ConfigurationSimplifier(object):
    def __init__(self, snapshot):
        bf_init_snapshot(snapshot, "origin", overwrite=True)
        load_questions()
        self.nodes = []
        results = bfq.nodeProperties().answer().frame()
        for _, result in results.iterrows():
            self.nodes.append(result.Node)

    def unreachable_switches(self, switches: List[str]) -> List[str]:
        pending_nodes = set(self.nodes)
        pending_nodes.difference_update(switches)
        for switch in switches:
            reserved = set()
            for pending_node in pending_nodes:
                results = bfq.reachability(
                    pathConstraints=PathConstraints(startLocation=switch, endLocation=pending_node)).answer().frame()
                if results.size == 0:
                    continue
                reserved.add(pending_node)
                for _, result in results.iterrows():
                    for trace in result.Traces:
                        for hop in trace.hops:
                            reserved.add(hop.node)
            pending_nodes.difference_update(reserved)
        return pending_nodes

