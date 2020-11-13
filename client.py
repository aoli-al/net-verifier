from pybatfish.client.commands import *
from pybatfish.question.question import load_questions
from pybatfish.question import bfq
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints

# def view_diff_frame(frame):
#   for flow in frame.Flow.tolist():
#     print(flow)
#   for traces in frame.Snapshot_Traces:
#     for t in traces:
#       print(t)

class Client(object):
  def setup_batfish(self):
    bf_session.host = 'localhost'

  def load_snapshot(self, snapshot_dir: str, name: str):
    bf_init_snapshot(snapshot_dir, name, overwrite=True)

  def check_traffic(self, snapshot: str, reference_snapshot: str):
    # bf_set_snapshot(name)
    load_questions()
    header = HeaderConstraints(srcIps="0.0.0.0/0", dstIps="0.0.0.0/0", ipProtocols=["tcp"])
    #  path = PathConstraints(startLocation="/as2/", endLocation="/as3/")
    result = bfq.differentialReachability(headers=header) \
        .answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()
    # result = bfq.reachability(headers=header, pathConstraints=path) \
    #     .answer(snapshot=reference_snapshot).frame()
    result.to_csv('out.csv')
    #  return result.count > 0
    #  print(result.to_string())
    # for idx, row in result.iterrows():
    #   view_diff_frame(row)

client = Client()
client.setup_batfish()
client.load_snapshot("/home/leo/repos/verifier/configs/origin", "origin")
client.load_snapshot("/home/leo/repos/verifier/configs/update1", "update1")
client.load_snapshot("/home/leo/repos/verifier/configs/update2", "update2")
#  client.check_traffic("origin", "update1")
client.check_traffic("origin", "update2")
