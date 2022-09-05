import numpy as np
from anytree import PostOrderIter


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
