from action import *
from resource import *
from condition import Condition
from models import HeaderConstraintBuilder, PathConstraintBuilder
from connectors import Connector
from pybatfish.question import bfq
from typing import List


# The user can do {action} for {resource} under {condition}.
class Policy(Connector):
    def __init__(self, action: List[Action], resource: List[Resource], condition: Condition = None):
        self.actions = action
        self.resources = resource
        self.condition = condition
        self.header_constraint = HeaderConstraintBuilder()
        self.path_constraint = PathConstraintBuilder()

    def build(self):
        self.build_header_constraint()
        self.build_path_constraint()

    def build_header_constraint(self):
        for action in self.actions:
            action.build_header_constraint(self.header_constraint)
        for resource in self.resources:
            resource.build_header_constraint(self.header_constraint)

    def build_path_constraint(self):
        for resource in self.resources:
            resource.build_path_constraint(self.path_constraint)

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        result = bfq.differentialReachability(
            header=self.header_constraint.build(), pathConstraints=self.path_constraint.build()) \
            .answer(snapshot=ori_snapshot, reference_snapshot=new_snapshot).frame()
        return result.size() > 0
