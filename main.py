import logging
from argparse import ArgumentParser

import coloredlogs as coloredlogs

import export
import procedures as p
from input import read_input
from node import Node


def main(args):
    # TODO:Candidates in re-encryption
    coloredlogs.install(
        level=args.loglevel, fmt='%(asctime)s [%(funcName)s] %(levelname)s %(message)s', datefmt='%H:%M:%S')
    print('Starting program...')
    # Manual assignment of assignee (used to simulate same execution contained in the paper)
    manual_assignment = args.manual_assignment
    # Read input data for the algorithm
    root, relations, subjects, authorizations, avg_comp_price, avg_transfer_price = read_input(args.input)
    export.export_tree(args.path + 'Plan.pdf', root)
    # Compute cost of any node assigned to any subject
    p.compute_cost(root, subjects)
    # Insert a node as parent of root assigned to the user formulating the query
    Node('query', Ap=set('CPI'), Ae=set(), enc_attr=set(), size=2, print_label='User formulating the query',
         children={root})
    root.parent.assignee = 'U'
    # Identify candidates for each node in the tree
    p.identify_candidates(root, subjects, authorizations)
    to_enc_dec = set()
    # Assign nodes to subjects and insert re-encryption operations
    p.compute_assignment(
        root, subjects, authorizations, to_enc_dec, relations, avg_comp_price, avg_transfer_price, manual_assignment)
    # Inject encryption/decryption operation
    p.extend_plan(root.root, subjects, authorizations)
    # Export results in a PDF documents
    export.export_tree(args.path + 'Tree.pdf', root.root)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--path", dest="path", help="Path where to save exported PDFs plans", metavar="PATH", required=True)
    parser.add_argument(
        "-m", "--manual", type=list, metavar='ASSIGNMENT',
        dest="manual_assignment", help="Manual assignment of candidates to nodes")
    parser.add_argument(
        "-i", "--input", metavar='INPUT', dest="input", help="Path from where read input", required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-v', '--verbose', help="Be verbose", action="store_const",
        dest="loglevel", const=logging.INFO, default=logging.WARNING)
    group.add_argument(
        '-d', '--debug', help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = parser.parse_args()
    main(args)
