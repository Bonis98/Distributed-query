from anytree import NodeMixin


class Ops:
    permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                     'group by', 'encryption', 'decryption', 're-encryption']

    def __init__(self, operation, attributes):
        if operation not in self.permitted_ops:
            raise ValueError("results: status must be one of %r." % self.permitted_ops)
        self.operation = operation
        self.attributes = attributes


class Node(Ops, NodeMixin):
    def __init__(self, operation, attributes, parent=None, children=None):
        super().__init__(operation, attributes)
        self.parent = parent
        if children:
            self.children = children
