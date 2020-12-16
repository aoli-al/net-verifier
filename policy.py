from action import Action
from resource import Resource
from condition import Condition
from models import HeaderConstraintBuilder, PathConstraintBuilder
from connectors import Connector
from pybatfish.question import bfq


## The user can do {action} for {resource} under {condition}.
class Policy(Connector):
    def __init__(self, action: Action, resource: Resource, condition: Condition):
        self.action = action
        self.resource = resource
        self.condition = condition
        self.header_constraint = HeaderConstraintBuilder()
        self.path_constraint = PathConstraintBuilder()

    def build(self):
        self.build_header_constraint()
        self.build_path_constraint()

    def build_header_constraint(self):
        self.action.build_header_constraint(self.header_constraint)
        self.resource.build_header_constraint(self.header_constraint)

    def build_path_constraint(self):
        self.resource.build_path_constraint(self.path_constraint)

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        result = bfq.differentialReachability(
            header=self.header_constraint, pathConstraints=self.path_constraint) \
            .answer(snapshot=ori_snapshot, reference_snapshot=new_snapshot).frame()
        return result.size() > 0

