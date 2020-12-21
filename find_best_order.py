from typing import List, FrozenSet
from pandas import DataFrame
from pathlib import Path
from pybatfish.client.commands import bf_init_snapshot
from pybatfish.question import bfq
from pybatfish.question.question import load_questions
import tempfile
import shutil
import os


class FindBestOrder(object):
    def __init__(self, base: Path, files: List[Path]):
        load_questions()
        self.base = base
        self.files = files
        self.cache = {}
        self.dp = {}
        self.path = {}
        self.current_idx = 0
        self.snapshots = {}
        self.diff_cache = {}
        self.tmp_folders = set()
        self.goal = self.get_or_create(frozenset(files))

    def get_snapshot(self, path: Path) -> str:
        if path not in self.snapshots:
            self.current_idx += 1
            bf_init_snapshot(str(path), str(self.current_idx))
            self.snapshots[path] = str(self.current_idx)
        return self.snapshots[path]

    def get_or_create(self, files: FrozenSet[Path]) -> Path:
        if files not in self.cache:
            directory = tempfile.TemporaryDirectory()
            base_path = os.path.join(directory.name, "snapshot")
            shutil.copytree(self.base, base_path)
            for file in files:
                shutil.copy(file, os.path.join(base_path, "configs"))
            self.cache[files] = Path(base_path)
            self.tmp_folders.add(directory)
        return self.cache[files]

    def get_cache_of_diff(self, origin: str, reference: str) -> DataFrame:
        if origin not in self.diff_cache:
            self.diff_cache[origin] = {}
        if reference not in self.diff_cache[origin]:
            self.diff_cache[origin][reference] = \
                bfq.differentialReachability().answer(snapshot=origin, reference_snapshot=reference).frame()
        return self.diff_cache[origin][reference]

    def get_diff(self, path: Path) -> int:
        snapshot = self.get_snapshot(path)
        goal = self.get_snapshot(self.goal)
        base = self.get_snapshot(self.base)
        goal_diff = self.get_cache_of_diff(goal, base)
        current_diff = self.get_cache_of_diff(goal, snapshot)
        return abs(goal_diff.size - current_diff.size)

    def find_recursive(self, files: FrozenSet[Path]) -> int:
        if not files:
            return 0
        if files not in self.dp:
            snapshot = self.get_or_create(files)
            current_min = 2 ** 32
            for file in files:
                candidate = files.difference([file])
                current_value = self.find_recursive(candidate)
                if current_value < current_min:
                    current_min = current_value
                    self.path[files] = candidate
            self.dp[files] = current_min + self.get_diff(snapshot)
        return self.dp[files]

    def show_path(self, start: FrozenSet[Path]) -> List[Path]:
        result = []
        current = start
        while current:
            prev = self.path[current]
            result.insert(0, next(iter(current.difference(prev))))
            current = prev
        return result


o = FindBestOrder(Path("/home/leo/repos/verifier/configs/test"),
                  [Path('/home/leo/repos/verifier/configs/updates/as1border1.cfg'),
                   Path('/home/leo/repos/verifier/configs/updates/as2border1.cfg')])
start = frozenset(o.files)
o.find_recursive(start)
print(o.show_path(start))
