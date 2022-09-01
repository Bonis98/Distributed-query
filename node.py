from anytree import NodeMixin


# Class representing an operation to be inserted in the tree plan
class Ops:
    # Value restriction for operation attribute
    permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                     'group-by', 'encryption', 'decryption', 're-encryption']

    def __init__(self, operation, plain_attr: set, re_enc_attr: set, enc_attr: set, group_attr=None):
        if operation not in self.permitted_ops:
            raise ValueError("Ops: operation must be one of %r." % self.permitted_ops)
        if not isinstance(enc_attr, set):
            raise TypeError("Ops: attributes must be a set, not %s" % type(enc_attr))
        if not isinstance(plain_attr, set):
            raise TypeError("Ops: plain_attr must be a set, not %s" % type(plain_attr))
        if not isinstance(re_enc_attr, set):
            raise TypeError("Ops: re_enc_attr must be a set, not %s" % type(re_enc_attr))
        if len(plain_attr.intersection(re_enc_attr).intersection(enc_attr)) != 0:
            raise ValueError("Ops: plain, re_enc and enc sets must be disjoint")
        if group_attr is not None:
            if not (plain_attr.union(re_enc_attr).union(enc_attr)).issuperset(group_attr):
                raise ValueError("Ops: group_attr must be a valid attribute")
            else:
                self.group_attr = group_attr
        self.plain_attr = plain_attr
        self.re_enc_attr = re_enc_attr
        self.enc_attr = enc_attr
        self.operation = operation

    # Returns all the attributes of an operation
    def get_attributes(self):
        return self.plain_attr.union(self.re_enc_attr).union(self.enc_attr)

    # Returns the attributes count of an operation
    def num_attr(self):
        return len(self.plain_attr.union(self.re_enc_attr).union(self.enc_attr))


# Class representing a node of the query plan
class Node(Ops, NodeMixin):
    vp = set()
    ve = set()
    vE = set()
    ip = set()
    ie = set()
    eq = set()

    def __init__(self, operation, plain_attr: set, re_enc_attr: set,
                 enc_attr: set, group_attr=None, parent=None, children=None):
        super().__init__(operation, plain_attr, re_enc_attr, enc_attr, group_attr)
        # Candidates authorized for query execution
        self.candidates = set()
        self.parent = parent
        if children:
            self.children = children

    def add_candidate(self, candidate):
        self.candidates.add(candidate)

    # Computes the profile of a node (in according to def 2.2)
    def compute_profile(self):
        # If node is a leaf, all attributes are encrypted in storage
        if self.is_leaf:
            self.vE = self.plain_attr.union(self.re_enc_attr).union(self.enc_attr)
        else:
            # Retrieve children of the node
            n = self.children
            if len(n) == 2:
                self.__assign_profile(n[0], n[1])
            else:
                self.__assign_profile(n[0])
        if len(self.plain_attr) > 0:
            self.vp = self.vp.union(self.plain_attr)
            self.ve = self.ve.difference(self.plain_attr)
            self.vE = self.vE.difference(self.plain_attr)
        if len(self.re_enc_attr) > 0:
            self.ve = self.ve.union(self.re_enc_attr)
            self.vE = self.vE.difference(self.re_enc_attr)
        if self.operation == 'projection':
            self.vp = self.vp.intersection(self.plain_attr)
            self.ve = self.ve.intersection(self.re_enc_attr)
            self.vE = self.vE.intersection(self.enc_attr)
        elif self.operation == 'selection' and self.num_attr() == 1:
            self.ip = self.ip.union(self.vp.intersection(self.plain_attr))
            self.ie = self.ve.union(self.vE).intersection(self.re_enc_attr.union(self.enc_attr)).union(self.ie)
        elif self.operation == 'selection' and self.num_attr() == 2:
            self.eq = self.eq.union(self.plain_attr)
            self.eq = self.eq.union(self.re_enc_attr)
            self.eq = self.eq.union(self.enc_attr)
        elif self.operation == 'join':
            self.eq = self.eq.union(self.plain_attr.union(self.enc_attr).union(self.re_enc_attr))
        elif self.operation == 'group-by':
            self.vp = self.vp.intersection(self.plain_attr)
            self.ve = self.ve.intersection(self.re_enc_attr)
            self.vE = self.vE.intersection(self.enc_attr)
            self.ip = self.vp.intersection(self.group_attr).union(self.ip)
            self.ie = self.ve.union(self.vE).intersection(self.group_attr).union(self.ie)

    def __assign_profile(self, n1, n2=None):
        # Retrieves profile from child(ren) node(s)
        self.vp = n1.vp
        self.ve = n1.ve
        self.vE = n1.vE
        self.ip = n1.ip
        self.ie = n1.ie
        self.eq = n1.eq
        if n2 is not None:
            self.vp = self.vp.union(n2.vp)
            self.ve = self.ve.union(n2.ve)
            self.vE = self.vE.union(n2.vE)
            self.ip = self.ip.union(n2.ip)
            self.ie = self.ie.union(n2.ie)
            self.eq = self.eq.union(n2.eq)
