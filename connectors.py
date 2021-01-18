class Connector(object):
    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        return False


class Or(Connector):
    def __init__(self, left: Connector, right: Connector):
        self.left = left
        self.right = right

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        return self.left.eval(ori_snapshot, new_snapshot) or \
            self.right.eval(ori_snapshot, new_snapshot)

    def __str__(self):
        return f"Or({self.left}, {self.right})"


class And(Connector):
    def __init__(self, left: Connector, right: Connector):
        self.left = left
        self.right = right

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        return self.left.eval(ori_snapshot, new_snapshot) and \
               self.right.eval(ori_snapshot, new_snapshot)

    def __str__(self):
        return f"And({self.left}, {self.right})"


class Not(Connector):
    def __init__(self, obj: Connector):
        self.obj = obj

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        return not self.obj.eval(ori_snapshot, new_snapshot)

    def __str__(self):
        return f"Not({self.obj})"
