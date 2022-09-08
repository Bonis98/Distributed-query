import numpy as np
from anytree import PostOrderIter
from subject import Subject
from node import Node


def compute_cost(root, subjects: set):
    # Matrix that stores costs
    comp_cost = np.zeros(((len(root.descendants) + 1), len(subjects)))
    for idx1, node in enumerate(PostOrderIter(root)):
        for idx2, subject in enumerate(subjects):
            comp_cost[idx1][idx2] += (subject.comp_price * int(node.get_comp_cost()))
            if node.is_leaf:
                continue
            # Cost of right child
            comp_cost[idx1][idx2] += comp_cost[idx1 - 1][idx2]
            # Cost of left child
            if len(node.children) == 2:
                # In order to retrieve cost of left child, extract right children and count number of its descendants
                right = node.children[1]
                n_children = len(right.descendants) + 1
                comp_cost[idx1][idx2] += comp_cost[idx1 - n_children - 1][idx2]
    return comp_cost


def identify_candidates(root, subjects: set):
    for node in PostOrderIter(root):
        if node.is_leaf:
            node.compute_profile()
            node.add_candidate(subjects)
            # No need to initialize totap and totae (already empty)
        else:
            node.compute_profile()
            for child in node.children:
                node.totAp = node.Ap.union(child.totAp)
                node.totAe = node.Ae.union(child.totAe)
            # Initialize candidates to empty set
            node.candidates = set()
            # Monotonicity property
            cand = subjects
            if len(node.children) == 1:
                if node.children[0].Ap.issubset(node.ip):
                    cand = node.children[0].candidates
            else:
                if node.children[0].Ap.union(node.children[1].Ap).issubset(node.ip):
                    cand = node.children[0].candidates
                    cand = cand.union(node.children[1].candidates)
            for subject in cand:
                # Authorized for current node
                if __is_authorized(subject, node):
                    # Authorized for first child of current node
                    if __is_authorized(subject, node.children[0]):
                        # If node has two children verify if it is authorized for it
                        if len(node.children) == 2:
                            # Authorized for second child (if present)
                            if __is_authorized(subject, node.children[1]):
                                node.candidates.add(subject)
                        # If node has one child, then subject is authorized
                        else:
                            node.candidates.add(subject)
            # If node has no candidates, print error stop the computation
            if len(node.candidates) == 0:
                print("No candidates available for node " + node.name)
                exit()


def __is_authorized(subject: Subject, node: Node):
    if not node.vp.union(node.ip).issubset(subject.plain_attr):
        return False
    if not node.ve.union(node.vE).union(node.ie).issubset(subject.enc_attr.union(subject.plain_attr)):
        return False
    for eq in node.eq:
        if not eq.issubset(subject.plain_attr):
            if not eq.issubset(subject.enc_attr):
                return False
    return True
