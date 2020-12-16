from models import HeaderConstraintBuilder, PathConstraintBuilder


class Resource(object):
    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        pass

    def build_path_constraint(self, builder: PathConstraintBuilder):
        pass


class CidrResource(Resource):
    def __init__(self, cidr: str):
        self.cidr = cidr

    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        builder.dstIps = self.cidr


class NamedResource(Resource):
    def __init__(self, name: str):
        self.name = name

    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        builder.dstIps = self.name


class PathResource(Resource):
    def __init__(self, path: str):
        self.path = path

    def build_path_constraint(self, builder: PathConstraintBuilder):
        builder.forbiddenLocations = self.path
