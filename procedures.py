import array
import math
from anytree import PostOrderIter, PreOrderIter
from subject import Subject
from node import Node


def compute_cost(root, subjects: list):
    for node in PostOrderIter(root):
        # Initialize array
        node.comp_cost = array.array('i', (0 for _ in range(0, len(subjects))))
        for idx, subject in enumerate(subjects):
            # Node cost
            node.comp_cost[idx] += (subject.comp_price * int(node.get_op_cost()))
            # Children costs
            for child in node.children:
                node.comp_cost[idx] += child.comp_cost[idx]


def identify_candidates(root, subjects: list):
    for node in PostOrderIter(root):
        node.candidates = list()
        if node.is_leaf:
            # Initializes profile to all empty but vE to all relation's attributes
            node.compute_profile()
            node.candidates = subjects.copy()
            # No need to initialize totap and totae (already empty)
        else:
            # Ap and Ae already initialized
            node.compute_profile()
            for child in node.children:
                node.totAp = node.Ap.union(child.totAp)
                node.totAe = node.Ae.union(child.totAe)
            # Initialize candidates to empty set
            node.candidates = list()
            # Monotonicity property
            cand = subjects.copy()
            if len(node.children) == 1:
                if node.children[0].Ap.issubset(node.ip):
                    cand = node.children[0].candidates.copy()
            else:
                if node.children[0].Ap.union(node.children[1].Ap).issubset(node.ip):
                    cand = node.children[0].candidates.copy()
                    for candidate in node.children[1].candidates:
                        if candidate not in cand:
                            cand.append(candidate)
            for subject in cand:
                # Authorized for current node
                if __is_authorized(subject, node):
                    # Authorized for first child of current node
                    if __is_authorized(subject, node.children[0]):
                        # If node has two children verify if it is authorized for it
                        if len(node.children) == 2:
                            # Authorized for second child (if present)
                            if __is_authorized(subject, node.children[1]):
                                node.candidates.append(subject)
                        # If node has one child, then subject is authorized
                        else:
                            node.candidates.append(subject)
            # If node has no candidates, print error stop the computation
            if len(node.candidates) == 0:
                print("No candidates available for node " + node.name)
                exit()


def compute_assignment(root, subjects: list, to_enc_dec: set,
                       relations: list, avg_comp_price: float,
                       avg_transfer_price: float, manual_assignment=None):
    for node in PreOrderIter(root):
        s_min = None
        min_cost = math.inf
        if node.is_leaf:
            # Assign node to the storage provider
            for subject in subjects:
                if subject.name == node.relation.storage_provider:
                    node.assignee = subject
                    break
            # Base relation of the node contains attributes to be re-encrypted
            if len(to_enc_dec.intersection(set(node.relation.attributes))):
                att = to_enc_dec.intersection(set(node.relation.attributes))
                cand = subjects.copy()
                while len(att) and len(cand):
                    # Candidates are already sorted by comp+transfer price
                    c = cand.pop(0)
                    dec = att.intersection(c.plain_attr)
                    if len(dec) and set(node.relation.attributes).issubset(set(c.plain_attr).union(set(c.enc_attr))):
                        # Insert re-encryption node for 'dec' as parent of current node
                        n = Node(operation="re-encryption", Ap=set(), Ae=dec, enc_attr=set(), size=2,
                                 re_encryption=True,
                                 print_label="Re-encrypt " + str(to_enc_dec.intersection(node.assignee.plain_attr)),
                                 parent=node.parent, children={node})
                        n.assignee = cand
                        att = att.difference(dec)
                if len(att):
                    print("Error: at least one attribute cannot be re-encrypted")
                    exit()
        elif not node.re_encryption:
            for cand in node.candidates:
                # Calculate transfer cost of relation
                if cand != node.parent.assignee:
                    cost = node.size * cand.transfer_price
                else:
                    cost = 0
                cost += node.comp_cost[subjects.index(cand)]    # Calculate computational cost
                for attr in node.totAp.union(node.totAe).intersection(cand.plain_attr):
                    for rel in relations:   # S decrypts the attribute
                        if attr in rel.attributes:
                            cost += int(rel.dec_costs[rel.attributes.index(attr)]) * cand.comp_price
                for attr in node.totAe.difference(cand.plain_attr):
                    for rel in relations:   # Need to delegate re-encryption of attribute
                        if attr in rel.attributes:
                            index = rel.attributes.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) * \
                                avg_comp_price + int(rel.size[index]) * (avg_transfer_price + int(cand.transfer_price))
                for attr in to_enc_dec.intersection(cand.plain_attr):   # S can re-encrypt attribute
                    for rel in relations:
                        if attr in rel.attributes:
                            index = rel.attributes.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) * cand.comp_price
                if cost < min_cost:
                    min_cost = cost
                    s_min = cand
            node.assignee = s_min   # Select subject with minimum cost for evaluate current node
            # Manual assignment, used only for debug
            if manual_assignment is not None:
                for subject in subjects:
                    if subject.name == manual_assignment[0]:
                        node.assignee = subject
                        manual_assignment.pop(0)
                        break
            # Insert re-encryption node for to_enc_dec attributes pushed down
            if len(to_enc_dec.intersection(node.assignee.plain_attr)):
                n = Node(operation="re-encryption", Ap=set(), Ae=to_enc_dec.intersection(node.assignee.plain_attr),
                         enc_attr=set(), size=2, re_encryption=True,
                         print_label="Re-encrypt " + str(to_enc_dec.intersection(node.assignee.plain_attr)),
                         parent=node.parent, children={node})
                n.assignee = node.assignee
                to_enc_dec = to_enc_dec.difference(s_min.plain_attr)
            to_enc_dec = to_enc_dec.union(node.Ae.difference(node.assignee.plain_attr))
            # Insert re-encryption node for attributes that need to be re-encrypted
            if len(node.Ae.intersection(node.assignee.plain_attr)):
                # Need to search correct path in the tree
                re_enc = node.Ae.intersection(node.assignee.plain_attr)
                for child in node.children:
                    for leaf in child.leaves:
                        path_attr = leaf.Ae.union(leaf.Ae).union(leaf.enc_attr).intersection(re_enc)
                        if len(path_attr):
                            n = Node(operation="re-encryption", Ap=set(), Ae=path_attr,
                                     enc_attr=set(), size=2, re_encryption=True,
                                     print_label="Re-encrypt " + str(path_attr),
                                     parent=node, children={child})
                            n.assignee = s_min


def __is_authorized(subject: Subject, node: Node):
    # Authorized for plaintext
    if not node.vp.union(node.ip).issubset(subject.plain_attr):
        return False
    # Authorized for encrypted
    if not node.ve.union(node.vE).union(node.ie).issubset(subject.enc_attr.union(subject.plain_attr)):
        return False
    # Uniform visibility
    for eq in node.eq:
        if not eq.issubset(subject.plain_attr):
            if not eq.issubset(subject.enc_attr):
                return False
    return True
