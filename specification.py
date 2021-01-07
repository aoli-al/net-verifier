from pathlib import Path
from typing import List, Dict, Set
from pybatfish.client.commands import bf_init_snapshot
from pybatfish.question.question import  load_questions
from command import Commands, NodeCommand
from connectors import Connector
from simplifier import ConfigurationSimplifier
from topology import TopologyBuilder, Topology
from utils import resolve
from policy import Policy
from action import *
from resource import *
import jsonpickle
import tempfile
import os
import shutil
import json


class Specification(object):
    def __init__(self,
                 config_path: Path,
                 accessible_nodes: Set[str],
                 sensitive_nodes: Set[str],
                 protected_nodes: Set[str],
                 topology: Topology,
                 commands: Dict[str, Set[str]],
                 invariants: Connector):
        self.config_path = config_path
        self.accessible_nodes = accessible_nodes
        self.sensitive_nodes = sensitive_nodes
        self.protected_nodes = protected_nodes
        self.topology = topology
        self.commands = commands
        self.invariants = invariants


class SpecificationBuilder(object):
    def __init__(self,
                 base: Path,
                 accessible_nodes: List[str],
                 protected_nodes: List[str],
                 sensitive_nodes: List[str],
                 allowed_command: Commands,
                 invariants: Connector):
        self.base = base
        bf_init_snapshot(str(base), "base")
        self.accessible_nodes = self.resolve(accessible_nodes, "base")
        self.protected_nodes = self.resolve(protected_nodes, "base")
        self.sensitive_nodes = self.resolve(sensitive_nodes, "base")
        self.allowed_command = allowed_command
        self.invariants = invariants

    def resolve(self, nodes: List[str], snapshot: str) -> Set[str]:
        resolved = [resolve(node, "", snapshot) for node in nodes]
        if not resolved:
            return set()
        else:
            return set.union(*resolved)

    def build(self) -> Specification:
        simplifier = ConfigurationSimplifier(self.base)
        unreachable_switches = simplifier.unreachable_switches(list(self.accessible_nodes))
        directory = tempfile.TemporaryDirectory()
        snapshot_path = os.path.join(directory.name, "snapshot")
        shutil.copytree(self.base, snapshot_path)
        for switch in unreachable_switches:
            os.remove(os.path.join(snapshot_path, 'configs', switch + '.cfg'))
        builder = TopologyBuilder(Path(snapshot_path))
        topology = builder.build()
        commands = self.allowed_command.compute()
        invariants = self.invariants
        return Specification(snapshot_path,
                             self.accessible_nodes,
                             self.protected_nodes,
                             self.sensitive_nodes,
                             topology,
                             commands,
                             invariants)


builder = SpecificationBuilder(Path("/home/leo/repos/sdn-verifier/configs/example"),
                               ['/as2core.*/'],
                               ['/as3.*/'],
                               [],
                               Commands([NodeCommand("/.*border.*/", "", {"aaa"}),
                                         NodeCommand("/.*core.*/", "", set("bbb"))]),
                               Policy([ApplicationAction("SSH")], [SrcIpResource("as2core2")], None))


load_questions()
specification = builder.build()
print(jsonpickle.encode(specification))

