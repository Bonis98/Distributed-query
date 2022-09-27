import sys

import export
import procedures as p
from input import read_input
from node import Node

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise ValueError("main: must specify tree and profile save path")
        exit(0)
    # Manual assignment of assignee (used to simulate same execution contained in the paper)
    if len(sys.argv) > 3:
        manual_assignment = list(sys.argv[3])
    # Read input data for the algorithm
    root, relations, subjects, authorizations, avg_comp_price, avg_transfer_price = read_input()
    # Compute cost of any node assigned to any subject
    p.compute_cost(root, subjects)
    # Insert a node as parent of root assigned to the user formulating the query
    Node('query', Ap=set('CPI'), Ae=set(), enc_attr=set(), size=2, print_label='User formulating query',
         children={root})
    root.parent.assignee = 'U'
    # Identify candidates for each node in the tree
    p.identify_candidates(root, subjects, authorizations)
    to_enc_dec = set()
    # Assign nodes to subjects and insert re-encryption operations
    p.compute_assignment(
        root, subjects, authorizations, to_enc_dec, relations, avg_comp_price, avg_transfer_price, manual_assignment)
    # Inject encryption/decryption operation
    p.extend_plan(root, subjects, authorizations)
    # Export results in two PDF documents
    export.export_tree('nodes', sys.argv[1] + 'Tree.pdf', root.parent)
    export.export_tree('profiles', sys.argv[2] + 'Profile.pdf', root)
