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


class And(Connector):
    def __init__(self, left: Connector, right: Connector):
        self.left = left
        self.right = right

    def eval(self, ori_snapshot: str, new_snapshot: str) -> bool:
        return self.left.eval(ori_snapshot, new_snapshot) and \
               self.right.eval(ori_snapshot, new_snapshot)
