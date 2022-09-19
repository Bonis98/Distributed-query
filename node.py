from anytree import NodeMixin


# Class representing an operation to be inserted in the tree plan
class Ops:
    def __init__(self, operation, Ap: set, Ae: set, enc_attr: set, group_attr=None):
        # Value restriction for operation attribute
        permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                         'group-by', 'encryption', 'decryption', 're-encryption', 'query']

        if operation not in permitted_ops:
            raise ValueError("Ops: operation must be one of %r." % permitted_ops)
        if not isinstance(enc_attr, set):
            raise TypeError("Ops: attributes must be a set, not %s" % type(enc_attr))
        if not isinstance(Ap, set):
            raise TypeError("Ops: Ap must be a set, not %s" % type(Ap))
        if not isinstance(Ae, set):
            raise TypeError("Ops: Ae must be a set, not %s" % type(Ae))
        if len(Ap.intersection(Ae).intersection(enc_attr)) != 0:
            raise ValueError("Ops: plain, re_enc and enc sets must be disjoint")
        if group_attr is not None:
            if not (Ap.union(Ae).union(enc_attr)).issuperset(group_attr):
                raise ValueError("Ops: group_attr must be a valid attribute")
            else:
                self.group_attr = group_attr
        self.Ap = Ap
        self.Ae = Ae
        self.enc_attr = enc_attr
        self.operation = operation

    # Returns all the attributes of an operation
    def get_attributes(self):
        return self.Ap.union(self.Ae).union(self.enc_attr)

    # Returns the attributes count of an operation
    def num_attr(self):
        return len(self.Ap.union(self.Ae).union(self.enc_attr))

    def get_op_cost(self):
        op_cost = {
            'projection': 1,
            'selection': 3,
            'cartesian': 5,
            'join': 5,
            'group-by': 2,
            'encryption': 2,
            'decryption': 2,
            're-encryption': 3
        }

        return int(op_cost[self.operation])


class Relation:
    def __init__(self, storage_provider, attributes: list, enc_costs: list, dec_costs: list, size: list):
        self.storage_provider = storage_provider
        if not (len(attributes) == len(enc_costs) == len(dec_costs) == len(size)):
            raise ValueError("Relation: attributes, enc_costs dec_costs and size must have the same length")
        self.attributes = attributes
        self.enc_costs = enc_costs
        self.dec_costs = dec_costs
        self.size = size


# Class representing a node of the query plan
class Node(Ops, NodeMixin):
    vp = set()
    ve = set()
    vE = set()
    ip = set()
    ie = set()
    eq = set()
    totAp = set()
    totAe = set()
    # Candidates authorized for query execution
    candidates = list()
    # Base relation
    relation = set()
    assignee = str()
    re_encryption = False
    comp_cost = dict()

    def __init__(self, operation, Ap: set, Ae: set, enc_attr: set, size=None, relation=None, re_encryption=False,
                 print_label=None, group_attr=None, parent=None, children=None):
        super().__init__(operation, Ap, Ae, enc_attr, group_attr)
        self.parent = parent
        self.re_encryption = re_encryption
        if operation != 're-encryption':
            if type(size) != int:
                raise TypeError("Node: size must be an integer, not %s" % type(size))
            self.size = size
        if relation is not None:
            self.relation = relation
        if print_label is not None:
            # Used to print the tree
            self.name = print_label
        if children:
            self.children = children

    # Computes the profile of a node (in according to def 2.2)
    def compute_profile(self):
        # If node is a leaf, all attributes are encrypted in storage
        if self.is_leaf:
            self.vp = set()
            self.ve = set()
            self.vE = self.Ap.union(self.Ae).union(self.enc_attr)
            self.ip = set()
            self.ie = set()
            self.eq = set()
        else:
            # Retrieve children of the node
            n = self.children
            if len(n) == 2:
                self.__assign_profile(n[0], n[1])
            else:
                self.__assign_profile(n[0])
        if len(self.Ap) > 0:
            self.vp = self.vp.union(self.Ap)
            self.ve = self.ve.difference(self.Ap)
            self.vE = self.vE.difference(self.Ap)
        if len(self.Ae) > 0:
            self.ve = self.ve.union(self.Ae)
            self.vE = self.vE.difference(self.Ae)
        if self.operation == 'projection':
            self.vp = self.vp.intersection(self.Ap)
            self.ve = self.ve.intersection(self.Ae)
            self.vE = self.vE.intersection(self.enc_attr)
        elif self.operation == 'selection' and self.num_attr() == 1:
            self.ip = self.ip.union(self.vp.intersection(self.Ap))
            self.ie = self.ve.union(self.vE).intersection(self.Ae.union(self.enc_attr)).union(self.ie)
        elif self.operation == 'selection' and self.num_attr() == 2:
            self.eq.add(frozenset(self.Ap.union(self.Ae).union(self.enc_attr)))
        elif self.operation == 'cartesian':
            # Union of sets of children, already done by __assign_profile
            pass
        elif self.operation == 'join':
            self.eq.add(frozenset(self.Ap.union(self.Ae).union(self.enc_attr)))
        elif self.operation == 'group-by':
            self.vp = self.vp.intersection(self.Ap)
            self.ve = self.ve.intersection(self.Ae)
            self.vE = self.vE.intersection(self.enc_attr)
            self.ip = self.vp.intersection(self.group_attr).union(self.ip)
            self.ie = self.ve.union(self.vE).intersection(self.group_attr).union(self.ie)

    def __assign_profile(self, n1, n2=None):
        # Retrieves profile from child(ren) node(s)
        self.vp = n1.vp.copy()
        self.ve = n1.ve.copy()
        self.vE = n1.vE.copy()
        self.ip = n1.ip.copy()
        self.ie = n1.ie.copy()
        self.eq = n1.eq.copy()
        if n2 is not None:
            self.vp = self.vp.union(n2.vp)
            self.ve = self.ve.union(n2.ve)
            self.vE = self.vE.union(n2.vE)
            self.ip = self.ip.union(n2.ip)
            self.ie = self.ie.union(n2.ie)
            self.eq = self.eq.union(n2.eq)
