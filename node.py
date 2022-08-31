from anytree import NodeMixin


class Ops:
    permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                     'group by', 'encryption', 'decryption', 're-encryption']
    plain = set()
    re_enc_attr = set()

    def __init__(self, operation, attributes: set, plain_attr: set, re_enc_attr: set):
        if operation not in self.permitted_ops:
            raise ValueError("Ops: operation must be one of %r." % self.permitted_ops)
        if not isinstance(attributes, set):
            raise TypeError("Ops: attributes must be a set, not %s" % type(attributes))
        if not isinstance(plain_attr, set):
            raise TypeError("Ops: plain_attr must be a set, not %s" % type(plain_attr))
        if not isinstance(re_enc_attr, set):
            raise TypeError("Ops: re_enc_attr must be a set, not %s" % type(re_enc_attr))
        self.operation = operation
        self.attributes = attributes
        if not plain_attr.issubset(attributes):
            raise ValueError("Plain set must be a subset of attributes set")
        self.plain = self.plain.union(plain_attr)
        if not re_enc_attr.issubset(attributes):
            raise ValueError("re-encryption set must be a subset of attributes set")
        self.re_enc_attr = self.re_enc_attr.union(re_enc_attr)


class Node(Ops, NodeMixin):
    def __init__(self, operation, attributes: set, plain_attr: set, re_enc_attr:set, parent=None, children=None):
        super().__init__(operation, attributes, plain_attr, re_enc_attr)
        self.candidates = set()
        self.parent = parent
        if children:
            self.children = children

    def add_candidate(self, candidate):
        self.candidates.add(candidate)

    def compute_profile(self):
        pass
