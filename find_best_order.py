from typing import List, FrozenSet
from pandas import DataFrame
from pathlib import Path
from pybatfish.client.commands import bf_init_snapshot
from pybatfish.question import bfq
from pybatfish.question.question import load_questions
from functools import cmp_to_key
import tempfile
import shutil
import os


class FindOrderBase(object):
    def __init__(self, base: Path, files: List[Path]):
        self.base = base
        self.files = files
        self.cache = {}
        self.current_idx = 0
        self.snapshots = {}
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

    def find(self) -> List[Path]:
        return self.files


class FindBestOrderPerCommand(FindOrderBase):

    def find(self) -> List[Path]:
        def compare(config1: Path, config2: Path):
            snapshot1 = self.get_snapshot(self.get_or_create(frozenset([config1])))
            snapshot2 = self.get_snapshot(self.get_or_create(frozenset([config2])))
            base = self.get_snapshot(self.base)
            diff1 = bfq.compareFilters().answer(snapshot=snapshot1, reference_snapshot=base).frame()
            action = ""
            for _, result in diff1.iterrows():
                action = result.Line_Action
            if action == "DENY":
                return 1
            diff2 = bfq.compareFilters().answer(snapshot=snapshot2, reference_snapshot=base).frame()
            for _, result in diff2.iterrows():
                action = result.Line_Action
            if action == "DENY":
                return -1
            elif action == "PERMIT":
                return 1
            else:
                return -1
        return sorted(self.files, key=cmp_to_key(compare))


class FindBestOrderPerFile(FindOrderBase):
    dp = {}
    path = {}
    diff_cache = {}

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
        current_diff = self.get_cache_of_diff(goal, snapshot)
        return current_diff.size

    def find(self) -> List[Path]:
        start = frozenset(self.files)
        self.find_recursive(start)
        return self.show_path(start)

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


load_questions()
o = FindBestOrderPerCommand(Path("/home/leo/repos/verifier/configs/default"),
                            [Path('/home/leo/repos/verifier/configs/updates/acls/as1border1.cfg'),
                             Path('/home/leo/repos/verifier/configs/updates/acls/as2border1.cfg')])
print(o.find())
