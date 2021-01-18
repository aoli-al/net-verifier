from typing import List, Set, Mapping
from pybatfish.question import bfq
from utils import interface_to_str, interfaces_from_snapshot
from pybatfish.client.commands import bf_init_snapshot
from topology import build_topology


class Base(object):
    def __init__(self, snapshot: str, affected_nodes: List[str]):
        self.snapshot = snapshot
        self.affected_nodes = affected_nodes
        self.interfaces = interfaces_from_snapshot(snapshot)

    def get_affected_interfaces(self) -> Set[str]:
        return self.interfaces


class Empty(Base):
    def get_affected_interfaces(self) -> Set[str]:
        return set()


class Neighbor(Base):
    def get_affected_interfaces(self) -> Set[str]:
        affected_interfaces = set()
        for node in self.affected_nodes:
            results = bfq.layer3Edges(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.add(interface_to_str(result.Remote_Interface))
        return affected_interfaces


class CrystalNet(Base):
    edge = set()

    def build_directed_graph(self) -> Mapping[str, Set[str]]:
        pending_nodes = []
        visited = set()
        poped = set()
        edge = {}
        for interface in self.interfaces:
            node_name = interface.split(":")[0]
            if "border" in node_name:
                pending_nodes.append(node_name)
                visited.add(node_name)
        while len(pending_nodes) > 0:
            node = pending_nodes.pop(0)
            poped.add(node)
            # if node not in edge:
            #     edge[node] = []
            results = bfq.layer3Edges(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                hostname = result.Remote_Interface.hostname
                if hostname not in edge:
                    edge[hostname] = set()
                if hostname not in poped:
                    edge[hostname].add(node)
                if hostname in visited:
                    continue
                pending_nodes.append(hostname)
                visited.add(hostname)
        return edge

    def get_affected_interfaces(self) -> Set[str]:
        edge = self.build_directed_graph()
        pending_nodes = self.affected_nodes.copy()
        affected_interfaces = []
        while len(pending_nodes) > 0:
            node = pending_nodes.pop(0)
            results = bfq.interfaceProperties(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.append(interface_to_str(result.Interface))
            if "border" in node:
                continue
            for parent in edge[node]:
                pending_nodes.append(parent)
        return set(affected_interfaces)


class Heimdall(Base):
    def get_affected_interfaces(self) -> Set[str]:
        t = build_topology(self.snapshot, set(self.affected_nodes), set())
        return t.reachable_nodes


class Harness(object):

    def __init__(self, base: str):
        self.base = base
        self.interfaces = interfaces_from_snapshot(base)

    def feasible(self):
        pass
