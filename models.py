from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints


class HeaderConstraintBuilder(object):
    def __init__(self):
        self.srcIps = None
        self.dstIps = None
        self.srcPorts = None
        self.dstPorts = None
        self.applications = None
        self.ipProtocols = None
        self.icmpCodes = None
        self.icmpTypes = None
        self.dscps = None
        self.ecns = None
        self.packetLenghts = None
        self.fragmentOffsets = None
        self.tcpFlags = None

    def build(self) -> HeaderConstraints:
        return HeaderConstraints(**self.__dict__)


class PathConstraintBuilder(object):
    def __init__(self):
        self.startLocation = None
        self.endLocation = None
        self.transitionLocations = None
        self.forbiddenLocations = None

    def build(self) -> PathConstraints:
        return PathConstraints(**self.__dict__)
