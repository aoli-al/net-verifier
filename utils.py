from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.primitives import Interface
from typing import Set


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


def interfaces_from_snapshot(snapshot: str) -> Set[str]:
    interfaces = set()
    results = bfq.interfaceProperties().answer(snapshot=snapshot).frame()
    for _, result in results.iterrows():
        interfaces.add(interface_to_str(result.Interface))
    return interfaces
