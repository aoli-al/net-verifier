from typing import List, Dict, Set
from pybatfish.question import bfq


class Command(object):

    def resolve(self) -> Dict[str, Set[str]]:
        return {}


class NodeCommand(Command):
    def __init__(self, node_spec: str, node_property: str, commands: Set[str]):
        self.node_spec = node_spec
        self.node_property = node_property
        self.commands = commands

    def resolve(self) -> Dict[str, Set[str]]:
        data = {}
        result = bfq.nodeProperties(nodes=self.node_spec,
                                    properties=self.node_property).answer().frame()
        for node in result.Node.values:
            data[node] = self.commands
        return data


class InterfaceCommand(Command):
    def __init__(self, node_spec: str, interface_spec: str, interface_property: str, commands: Set[str]):
        self.node_spec = node_spec
        self.interface_spec = interface_spec
        self.interface_property = interface_property
        self.commands = commands

    def resolve(self):
        data = {}
        result = bfq.interfaceProperties(nodes=self.node_spec,
                                         interfaces=self.interface_spec,
                                         properties=self.interface_property).answer().frame()
        for node in result.Interface.values:
            data[node.hostname] = self.commands
        return data


class Commands(object):
    def __init__(self, commands: List[Command]):
        self.commands = commands

    def compute(self) -> Dict[str, Set[str]]:
        result = {}
        for command in self.commands:
            for (key, value) in command.resolve().items():
                if key not in result:
                    result[key] = value
                else:
                    result[key] = result[key].union(value)
        return result


