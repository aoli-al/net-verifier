from pathlib import Path
from pybatfish.question import bfq
from pybatfish.client.commands import bf_init_snapshot


class Topology(object):
    nodes = set()
    links = []


class TopologyBuilder(object):
    def __init__(self, base: Path):
        self.base = base

    def build(self) -> Topology:
        bf_init_snapshot(str(self.base), "topo")
        topology = Topology()
        results = bfq.layer3Edges().answer(snapshot="topo").frame()
        for _, result in results.iterrows():
            topology.nodes.add(result.Interface)
            topology.nodes.add(result.Remote_Interface)
            topology.links.append((result.Interface, result.Remote_Interface))
        return topology

