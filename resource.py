from models import HeaderConstraintBuilder, PathConstraintBuilder


class Resource(object):
    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        pass

    def build_path_constraint(self, builder: PathConstraintBuilder):
        pass


class SrcIpResource(Resource):
    def __init__(self, src_ip: str):
        self.src_ip = src_ip

    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        builder.srcIps = self.src_ip


class DstIpResource(Resource):
    def __init__(self, dst_ip: str):
        self.dst_ip = dst_ip

    def build_header_constraint(self, builder: HeaderConstraintBuilder):
        builder.dstIps = self.dst_ip


class StartLocationResource(Resource):
    def __init__(self, start_location: str):
        self.start_location = start_location

    def build_path_constraint(self, builder: PathConstraintBuilder):
        builder.startLocation = self.start_location


class EndLocationResource(Resource):
    def __init__(self, end_location: str):
        self.end_location = end_location

    def build_path_constraint(self, builder: PathConstraintBuilder):
        builder.endLocation = self.end_location


class TransitLocationResource(Resource):
    def __init__(self, transit_location: str):
        self.transit_location = transit_location

    def build_path_constraint(self, builder: PathConstraintBuilder):
        builder.transitionLocations = self.transit_location


class ForbiddenLocationResource(Resource):
    def __init__(self, forbidden_location: str):
        self.forbidden_location = forbidden_location

    def build_path_constraint(self, builder: PathConstraintBuilder):
        builder.forbiddenLocations = self.forbidden_location
