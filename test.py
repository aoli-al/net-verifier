from pybatfish.question import bfq
from pybatfish.question.question import load_questions
from pybatfish.client.commands import bf_init_snapshot

load_questions()
bf_init_snapshot("/home/leo/repos/verifier/configs/default", "t1")
bf_init_snapshot("/home/leo/repos/verifier/configs/test", "t2")

results = bfq.differentialReachability().answer(snapshot="t1", reference_snapshot="t2").frame()
print(results.size)
for idx, result in results.iterrows():
    print(result.Flow)
