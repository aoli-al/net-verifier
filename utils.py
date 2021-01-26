from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.client.commands import bf_init_snapshot, bf_delete_snapshot
from pybatfish.datamodel.primitives import Interface
from typing import Set, List, Dict
import os
import json


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


def nodes_from_snapshot(snapshot: str) -> Set[str]:
    interfaces = interfaces_from_snapshot(snapshot)
    return set([i.split(":")[0] for i in interfaces])


def interfaces_from_snapshot(snapshot: str, nodes: str = None) -> Set[str]:
    cache_path = os.path.join(snapshot, "interface_from_snapshot.json")
    found = False
    if os.path.exists(cache_path):
        found = True
        caches = json.load(open(cache_path))
    else:
        bf_init_snapshot(snapshot, "interface_from_snapshot", overwrite=True)
        caches = {}
    if len(caches) == 0:
        results = bfq.interfaceProperties().answer(snapshot="interface_from_snapshot").frame()
        for _, result in results.iterrows():
            if result.Interface.hostname not in caches:
                caches[result.Interface.hostname] = []
            caches[result.Interface.hostname].append(interface_to_str(result.Interface))
    json.dump(caches, open(cache_path, "w"))
    if not found:
        bf_delete_snapshot("interface_from_snapshot")
    if nodes:
        return set(caches[nodes])
    else:
        return set([y for x in caches.values() for y in x])


def remove_interface_in_config(config: str, node_and_interfaces: List[str]):
    for node_and_interface in node_and_interfaces:
        [node, interface] = node_and_interface.split(":")
        if "host" in node or "pc" in node:
            os.remove(os.path.join(config, "hosts", node + ".json"))
        else:
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

