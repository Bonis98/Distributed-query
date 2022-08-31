from anytree import NodeMixin


class Ops:
    permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                     'group by', 'encryption', 'decryption', 're-encryption']

    def __init__(self, operation, attributes: set):
        if operation not in self.permitted_ops:
            raise ValueError("Ops: operation must be one of %r." % self.permitted_ops)
        if not isinstance(attributes, set):
            raise TypeError("Ops: attributes must be a set, not %s" % type(attributes))
        self.operation = operation
        self.attributes = attributes


class Node(Ops, NodeMixin):
    def __init__(self, operation, attributes, parent=None, children=None):
        super().__init__(operation, attributes)
        self.parent = parent
        if children:
            self.children = children
