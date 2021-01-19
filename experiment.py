from typing import List, Set, Tuple, Generator, Dict, Any
from pybatfish.question import bfq
from utils import interface_to_str, interfaces_from_snapshot
from pybatfish.client.commands import bf_init_snapshot
from topology import build_topology
import os
import shutil
import tempfile
import json


class Base(object):
    def __init__(self, snapshot: str, affected_nodes: List[str]):
        self.snapshot = snapshot
        self.affected_nodes = affected_nodes
        self.interfaces = interfaces_from_snapshot(snapshot)

    def get_internal_interfaces(self) -> Set[str]:
        return self.interfaces

    def get_internal_nodes(self) -> Set[str]:
        interfaces = self.get_internal_interfaces()
        return set([interface.split(":")[0] for interface in interfaces])


class Empty(Base):
    def get_internal_interfaces(self) -> Set[str]:
        return set()


class Neighbor(Base):
    def get_internal_interfaces(self) -> Set[str]:
        affected_interfaces = set()
        for node in self.affected_nodes:
            results = bfq.layer3Edges(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.add(interface_to_str(result.Remote_Interface))
        return affected_interfaces


class CrystalNet(Base):
    edge = set()

    def build_directed_graph(self) -> Dict[str, Set[str]]:
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

    def get_internal_interfaces(self) -> Set[str]:
        edge = self.build_directed_graph()
        pending_nodes = self.affected_nodes.copy()
        affected_interfaces = []
        while len(pending_nodes) > 0:
            node = pending_nodes[0]
            pending_nodes = pending_nodes[1:]
            results = bfq.interfaceProperties(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.append(interface_to_str(result.Interface))
            if "border" in node:
                continue
            if node not in edge:
                continue
            for parent in edge[node]:
                pending_nodes.append(parent)
        return set(affected_interfaces)


class Heimdall(Base):
    def get_internal_interfaces(self) -> Set[str]:
        t = build_topology(self.snapshot, set(self.affected_nodes), set())
        return t.reachable_nodes


class Harness(object):

    solutions = [
        (Base, "base"),
        (Empty, "empty"),
        (Neighbor, "neighbor"),
        (CrystalNet, "crystal-net"),
        (Heimdall, "heimdall")
    ]

    def __init__(self, base: str):
        self.base = base
        bf_init_snapshot(base, "exp")
        self.interfaces = interfaces_from_snapshot("exp")
        self.name_idx = 0

    def get_affected_node(self, node: str, snapshot: str) -> Set[str]:
        affected_node = set()
        self.name_idx += 1
        results = bfq.differentialReachability().answer(snapshot=snapshot, reference_snapshot="exp").frame()
        for idx, result in results.iterrows():
            if result.Flow.ingressNode is not None and result.Flow.ingressNode != node:
                affected_node.add(result.Flow.ingressNode)
        return affected_node

    def generate_test_case(self) -> Generator[Tuple[str, Set[str], str], None, None]:
        for interface_name in self.interfaces:
            [node, interface] = interface_name.split(":")
            if "host" in node:
                continue
            dir = tempfile.TemporaryDirectory()
            shutil.copytree(self.base, dir.name+"/", dirs_exist_ok=True)
            file = os.path.join(dir.name, "configs", node + ".cfg")
            lines = []
            skip = False
            for line in open(file):
                if line.strip() == "!" and skip:
                    skip = False
                    continue
                if f"interface {interface}" in line:
                    skip = True
                    continue
                if skip:
                    continue
                lines.append(line)
            with open(file, "w") as f:
                for line in lines:
                    f.write(line)
            snapshot = f"exp_{self.name_idx}"
            bf_init_snapshot(dir.name, f"exp_{self.name_idx}")
            nodes = self.get_affected_node(node, snapshot)
            if len(nodes):
                yield interface_name, nodes, snapshot

    def run(self) -> List[Dict[str, Any]]:
        results = []
        for interface, affected_nodes, snapshot in self.generate_test_case():
            print(f"Interface {interface} is down.")
            result = {
                "interface": interface,
                "affected_nodes": list(affected_nodes),
                "solutions": []
            }
            for solution, name in self.solutions:
                s = solution(snapshot, list(affected_nodes))
                internal_nodes = s.get_internal_nodes()
                result['solutions'].append({
                    "name": name,
                    "internal_nodes": list(internal_nodes),
                })
            results.append(result)
        return results

def process_json(path: str):
    out = open('out.csv', 'w')
    result = json.load(open("out.json"))
    for case in result:
        for solution in case['solutions']:
            out.write(f"{case['interface']}, {len(case['affected_nodes'])}, {solution['name']}, "
                      f"{len(solution['internal_nodes'])}, "
                      f"{case['interface'].split(':')[0] in solution['internal_nodes']}\n")


