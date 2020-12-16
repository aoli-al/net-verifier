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


class PathConstraintBuilder(object):
    def __init__(self):
        self.startLocation = ""
        self.endLocation = ""
        self.transitionLocations = ""
        self.forbiddenLocations = ""
