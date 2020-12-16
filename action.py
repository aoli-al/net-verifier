from typing import List

from models import HeaderConstraintBuilder


class Action(object):
    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        pass


class ApplicationAction(Action):
    def __init__(self, application_name: str):
        self.application_name = application_name

    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        header_constraint.applications.append(self.application_name)


class SrcPortAction(Action):
    def __init__(self, port_number: str):
        self.port_number = port_number

    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        header_constraint.srcPorts = str(self.port_number)


class DstPortAction(Action):
    def __init__(self, port_number: str):
        self.port_number = port_number

    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        header_constraint.dstPorts = str(self.port_number)


class IpProtocolAction(Action):
    def __init__(self, ip_protocol: List[str]):
        self.ip_protocol = ip_protocol

    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        header_constraint.ipProtocols = self.ip_protocol


class IcmpAction(Action):
    def __init__(self, code: List[int], t: List[int]):
        self.code = code
        self.type = t

    def build_header_constraint(self, header_constraint: HeaderConstraintBuilder):
        header_constraint.icmpCodes = self.code
        header_constraint.icmpTypes = self.type

