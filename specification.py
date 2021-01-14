from pathlib import Path
from typing import List, Dict, Set, Any
from pybatfish.client.commands import bf_init_snapshot
from pybatfish.question.question import  load_questions
from command import Commands, NodeCommand
from connectors import Connector
from topology import build_topology, Topology
from utils import resolve
from policy import Policy
from action import *
from resource import *
import jsonpickle


class Specification(object):
    def __init__(self,
                 config_path: Path,
                 sensitive_nodes: Set[str],
                 topology: Topology,
                 commands: Dict[str, Set[str]],
                 invariants: Connector,
                 ticket: str):
        self.config_path = config_path
        self.sensitive_nodes = sensitive_nodes
        self.topology = topology
        self.commands = commands
        self.invariants = invariants
        self.ticket = ticket


def resolve_list(nodes: List[str], snapshot: str) -> Set[str]:
    resolved = [resolve(node, "", snapshot) for node in nodes]
    if not resolved:
        return set()
    else:
        return set.union(*resolved)


def build_specification(base: Path, affected_nodes: List[str], sensitive_nodes: List[str],
                        allowed_command: Commands, invariants: Connector) -> Specification:
    bf_init_snapshot(str(base), "base")
    affected_nodes = resolve_list(affected_nodes, "base")
    sensitive_nodes = resolve_list(sensitive_nodes, "base")
    topology = build_topology(Path(base), affected_nodes, sensitive_nodes)
    commands = allowed_command.compute()
    return Specification(base,
                         sensitive_nodes,
                         topology,
                         commands,
                         invariants,
                         "")


def build_specification_from_dict(data: Dict[str, Any]):
    return build_specification(data["base"], data["affected_nodes"], data["sensitive_nodes"],
                               Commands([eval(command) for command in data["allowed_command"]]),
                               eval(data["invariants"]))


# specification = build_specification(base=Path("/home/leo/repos/sdn-verifier/configs/example"),
#                                     affected_nodes=['/as2core.*/'],
#                                     sensitive_nodes=['as2dist1'],
#                                     allowed_command=Commands([NodeCommand("/.*border.*/", "", {"aaa"}),
#                                                               NodeCommand("/.*core.*/", "", {"bbb"})]),
#                                     invariants=Policy([ApplicationAction("SSH")], [SrcNodeResource("host1"),
#                                                                                    DstNodeResource("as2core2")]))

data = {
    "base": "/home/leo/repos/sdn-verifier/configs/example",
    "affected_nodes": ['/as2core.*/'],
    "sensitive_nodes": ['as2dist1'],
    "allowed_command": ["NodeCommand(\"/.*border.*/\", \"\", {\"up\"})",
                        "NodeCommand(\"/.*core.*/\", \"\", {\"login\"})"],
    "invariants": "Policy([ApplicationAction(\"SSH\")], [SrcNodeResource(\"host1\"), DstNodeResource(\"as2core2\")])"
}

load_questions()
specification = build_specification_from_dict(data)
print(jsonpickle.encode(specification, indent=2))

# Link
# if all interface are accessible -> accessible link
# if one i is sensitive -> sensitive link
# if one interface is protected -> protected link

# ProtectedNode <- Unreachable AffectedNodes
#
# AccessibleNodes + ProtectedNodes = World
# AccessibleNodes = World - ProtectedNodes
# World = Topology.nodes

# Ticket information, affected nodes
# Unreachable nodes
