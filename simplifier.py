from pybatfish.client.commands import *
from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints

bf_session.host = 'localhost'
bf_init_snapshot("/home/leo/repos/verifier/configs/default", "origin", overwrite=True)
load_questions()

result = bfq.traceroute(startLocation='@enter(as2border1[GigabitEthernet2/0])',
                        headers=HeaderConstraints(dstIps='0.0.0.0/0', srcIps='0.0.0.0/0')).answer().frame()
