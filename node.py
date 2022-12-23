import logging

from anytree import NodeMixin


# Class representing an operation to be inserted in the tree plan
class Ops:
    def __init__(self, operation, Ap: set, Ane: set, Ae: set, As: set, group_attr, select_multi_attr):
        # Value restriction for operation attribute
        permitted_ops = [
            'projection', 'selection', 'cartesian', 'join',
            'group-by', 'encryption', 'decryption', 're-encryption', 'query']
        Ap = set(Ap)
        Ae = set(Ae)
        As = set(As)
        Ane = set(Ane)
        if operation.lower() not in permitted_ops:
            raise ValueError('Ops: operation must be one of %r.' % permitted_ops)
        if operation.lower() == 'selection':
            self.select_multi_attr = select_multi_attr
        else:
            self.select_multi_attr = False
        if len(Ap.intersection(Ae, As)):
            raise ValueError('Ops: plain, re_enc and enc sets must be disjoint')
        if not Ane.issubset(Ap):
            raise ValueError('Ops: Ane must be a subset of Ap')
        if group_attr is not None:
            if not (Ap.union(Ae, As)).issuperset(group_attr):
                raise ValueError('Ops: group_attr must be a valid attribute')
            else:
                self.group_attr = group_attr
        self.Ap = Ap
        self.Ae = Ae
        self.As = As
        self.Ane = Ane
        self.operation = operation.lower()

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
    attributes = set()
    # Candidates authorized for query execution
    candidates = list()
    # Base relation
    relation = None
    assignee = str()
    comp_cost = dict()

    def __init__(
            self, operation, cryptographic=False, print_label=None, group_attr=None, select_multi_attr=False,
            parent=None, children=None, Ane=None, Ap=None, Ae=None, As=None):
        if As is None:
            As = set()
        if Ae is None:
            Ae = set()
        if Ap is None:
            Ap = set()
        if Ane is None:
            Ane = set()
        super().__init__(operation, Ap, Ane, Ae, As, group_attr, select_multi_attr)
        self.parent = parent
        self.cryptographic = cryptographic
        self.size = 0
        if print_label is not None:
            # Used to print the tree
            self.name = print_label
        if children:
            self.children = children
        self.attributes = set(Ap).union(set(Ae)).union(set(As))

    # Computes the profile of a node (according to def 2.2)
    def compute_profile(self):
        logging.debug('Computing profile for node %s', self.name)
        self.vp = set()
        self.ve = set()
        self.vE = set()
        self.ip = set()
        self.ie = set()
        self.eq = set()
        # leaf nodes are projections
        if self.is_leaf:
            self.vp = set(self.relation.plain_attr)
            self.ve = set()
            self.vE = set(self.relation.enc_attr)
            self.ip = set()
            self.ie = set()
            self.eq = set()
        else:
            # Copy profiles from children
            for child in self.children:
                self.vp = self.vp.union(child.vp)
                self.ve = self.ve.union(child.ve)
                self.vE = self.vE.union(child.vE)
                self.ip = self.ip.union(child.ip)
                self.ie = self.ie.union(child.ie)
                self.eq = self.eq.union(child.eq)
        # If an attribute has to be evaluated in plain, add it to vp
        if len(self.Ane) and not self.cryptographic:
            self.vp = self.vp.union(self.Ane)
            self.ve = self.ve.difference(self.Ane)
            self.vE = self.vE.difference(self.Ane)
        # If an attribute has to be evaluated re-encrypted, add it to ve
        if len(self.Ae) and not self.cryptographic:
            self.vp = self.vp.difference(self.Ae.difference(self.Ap))
            self.ve = self.ve.union(self.Ae.difference(self.Ap))
            self.vE = self.vE.difference(self.Ae.difference(self.Ap))
        # Start to calculate profiles
        if self.operation == 'projection':
            self.vp = self.vp.intersection(self.attributes)
            self.ve = self.ve.intersection(self.attributes)
            self.vE = self.vE.intersection(self.attributes)
        elif self.operation == 'selection' and not self.select_multi_attr:
            self.ip = self.ip.union(self.vp.intersection(self.attributes))
            self.ie = self.ie.union(self.ve.union(self.vE).intersection(self.attributes))
        elif self.operation == 'selection' and self.select_multi_attr:
            self.eq.add(frozenset(self.attributes))
        elif self.operation == 'cartesian':
            # Union of sets of children, already done by __assign_profile
            pass
        elif self.operation == 'join':
            # Union of first 5 sets already done by __assign_profile
            self.eq.add(frozenset(self.attributes))
        elif self.operation == 'group-by':
            self.vp = self.vp.intersection(self.attributes)
            self.ve = self.ve.intersection(self.attributes)
            self.vE = self.vE.intersection(self.attributes)
            self.ip = self.ip.union(self.vp.intersection(self.group_attr))
            self.ie = self.ie.union(self.ve.union(self.vE).intersection(self.group_attr))
        elif self.operation == 'encryption':
            # Enc nodes have all attributes in Ap
            self.vp = self.vp.difference(self.attributes)
            self.ve = self.ve.union(self.attributes)
        elif self.operation == 'decryption':
            # Dec nodes have all attributes in Ae
            self.vp = self.vp.union(self.attributes)
            self.ve = self.ve.difference(self.attributes)
            self.vE = self.vE.difference(self.attributes)
        elif self.operation == 're-encryption':
            # Re_enc nodes have all attributes in Ae
            self.ve = self.ve.union(self.attributes)
            self.vE = self.vE.difference(self.attributes)
