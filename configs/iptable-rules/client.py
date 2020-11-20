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

  def get_traffic(self, snapshot: str):
    load_questions()
    result = bfq.reachability(headers=self.header, pathConstraints=self.path) \
        .answer(snapshot=snapshot).frame()
    print(result.to_csv("path.csv"))
    # if result.
    # result.to_csv("path.csv")

  def check_traffic(self, snapshot: str, reference_snapshot: str):
    # bf_set_snapshot(name)
    load_questions()
    result = bfq.differentialReachability(headers=self.header, pathConstraints=self.path) \
        .answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()
    result.to_csv('diff.csv')

  def __init__(self):
    self.header = HeaderConstraints(dstIps="host1", dstPorts="22")
    self.path = PathConstraints(startLocation="/as3/")

client = Client()
client.setup_batfish()
client.load_snapshot("./origin", "origin")
client.load_snapshot("./allowed", "allowed")
client.load_snapshot("./denied", "denied")
#  client.check_traffic("origin", "update1")
client.check_traffic("origin", "allowed")
client.get_traffic('origin')
