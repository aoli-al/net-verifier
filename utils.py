from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.primitives import Interface
from typing import Set, List, Dict
import os


def resolve(node_spec: str, node_property: str, snapshot: str):
    data = set()
    load_questions()
    result = bfq.nodeProperties(nodes=node_spec,
                                properties=node_property)\
        .answer(snapshot=snapshot).frame()
    for node in result.Node.values:
        data.add(node)
    return data


def interface_to_str(interface: Interface) -> str:
    return f"{interface.hostname}:{interface.interface}"

def interface_map(snapshot: str) -> Dict[str, Set[str]]:
    for node_and_interface in interfaces_from_snapshot(snapshot):
        pass

def interfaces_from_snapshot(snapshot: str, nodes: str = None) -> Set[str]:
    interfaces = set()
    if nodes:
        results = bfq.interfaceProperties(nodes=nodes).answer(snapshot=snapshot).frame()
    else:
        results = bfq.interfaceProperties().answer(snapshot=snapshot).frame()
    for _, result in results.iterrows():
        interfaces.add(interface_to_str(result.Interface))
    return interfaces


def remove_interface_in_config(config: str, node_and_interfaces: List[str]):
    for node_and_interface in node_and_interfaces:
        [node, interface] = node_and_interface.split(":")
        file = os.path.join(config, "configs", node + ".cfg")
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


