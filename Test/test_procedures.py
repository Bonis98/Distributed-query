import io

import pandas as pd
from anytree import RenderTree

from export import export_tree
from node import Node
from procedures import compute_cost, __is_authorized, identify_candidates, compute_assignment
from relation import Relation


def test_compute_cost():
    # Create a tree with only one node
    root = Node(operation='selection', Ap=set(), Ae=set(), enc_attr=set(), size=2)
    # Create two subjects with different computational price
    csv_data = io.StringIO('subject,comp_price\nU,1\nX,2')
    df = pd.read_csv(csv_data)
    subjects = df.set_index('subject').T.to_dict('dict')
    compute_cost(root, subjects)
    node = root
    # Check len and value of computational cost computed
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 3
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 3
    # Add a child node
    Node(operation='projection', Ap=set(), Ae=set(), enc_attr=set(), size=2, parent=root)
    compute_cost(root, subjects)
    # Check child
    node = root.children[0]
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 1
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 1
    # Check parent
    node = root
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 3 + node.children[0].comp_cost['U']
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 3 + node.children[0].comp_cost['X']
    # Add a second child node
    Node(operation='join', Ap=set(), Ae=set(), enc_attr=set(), size=2, parent=root)
    compute_cost(root, subjects)
    # Check first child (projection)
    node = root.children[0]
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 1
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 1
    # Check second child (join)
    node = root.children[1]
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 5
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 5
    # Check parent
    node = root
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] \
           * 3 \
           + node.children[0].comp_cost['U'] \
           + node.children[1].comp_cost['U']
    assert node.comp_cost['X'] == df['comp_price'].values[1] \
           * 3 \
           + node.children[0].comp_cost['X'] \
           + node.children[1].comp_cost['X']


def test_is_authorized():
    # Create a tree with only one node
    root = Node(operation='selection', Ap=set(), Ae=set(), enc_attr=set(), size=2)
    # Assign a profile
    root.vp = set('JI')
    root.ve = set('NSC')
    root.eq = set()
    root.eq.add(frozenset('JS'))
    # Create three subjects with different authorizations
    csv_data = io.StringIO('subject,plain,enc\nU,NCPSJI,\nX,PC,NSJI\nY,JI,NS\nZ,DPJI,CNS')
    df = pd.read_csv(csv_data).fillna(value='')
    authorization = df.set_index('subject').T.to_dict('dict')
    # Authorized
    assert __is_authorized(authorization['U'], root)
    # No plain visibility
    assert not __is_authorized(authorization['X'], root)
    # No enc visibility
    assert not __is_authorized(authorization['Y'], root)
    # No uniform visibility
    assert not __is_authorized(authorization['Z'], root)


def test_identify_candidates():
    # Create three subjects
    csv_data = io.StringIO('subject,comp_price,transfer_price\nX,1,1\nY,2,2\nZ,3,3')
    df = pd.read_csv(csv_data)
    subjects = df.set_index('subject').T.to_dict('dict')
    # Create three authorizations
    csv_data = io.StringIO('subject,plain,enc\nX,CD,S\nY,NP,SD\nZ,NS,DP')
    df = pd.read_csv(csv_data)
    authorizations = df.set_index('subject').T.to_dict('dict')
    # Create a base relation
    r = Relation(storage_provider='S', attributes='NPSD', enc_costs='1234', dec_costs='1234', size='1234')
    # Create a light query plan
    root = Node(operation='join', Ap=set('NS'), Ae=set(), enc_attr=set(), size=2)
    root.relation = r
    Node(operation='projection', Ap=set(), Ae=set('NP'), enc_attr=set(), size=2, parent=root)
    Node(operation='projection', Ap=set(), Ae=set('SD'), enc_attr=set(), size=2, parent=root)
    for child in root.children:
        child.relation = r
        child.compute_profile()
    root.compute_profile()
    identify_candidates(root, subjects, authorizations)
    # Leaf nodes have all subjects as candidates
    assert root.children[0].candidates == list('XYZ')
    assert root.children[1].candidates == list('XYZ')
    assert root.candidates == list('Z')


def test_compute_assignment():
    # Create three subjects
    csv_data = io.StringIO('subject,comp_price,transfer_price\nX,1,1\nY,2,2\nZ,3,3')
    df = pd.read_csv(csv_data)
    subjects = df.set_index('subject').T.to_dict('dict')
    # Create three authorizations
    csv_data = io.StringIO('subject,plain,enc\nX,NS,PD\nY,NP,SD\nZ,,NS')
    df = pd.read_csv(csv_data)
    df = df.fillna(value='')
    authorizations = df.set_index('subject').T.to_dict('dict')
    # Create a base relation
    r = Relation(storage_provider='S', attributes='NPSD', enc_costs='1234', dec_costs='1234', size='1234')
    # Create a light query plan
    root = Node(operation='join', Ap=set(), Ae=set('NS'), enc_attr=set(), size=2)
    n = Node(operation='projection', Ap=set(), Ae=set(), enc_attr=set('NP'), size=2, parent=root)
    n.relation = r
    n = Node(operation='projection', Ap=set(), Ae=set(), enc_attr=set('SD'), size=2, parent=root)
    n.relation = r
    # Set of re-encryption attributes
    to_enc_dec = set()
    # List of base relations
    relations = list()
    relations.append(r)
    # Manual assignment of assignees
    manual_assignment = list('XYZ')
    compute_assignment(
        root=root, subjects=subjects, authorizations=authorizations, to_enc_dec=to_enc_dec, relations=relations,
        avg_comp_price=3, avg_transfer_price=3, manual_assignment=manual_assignment)
    # Procedure should insert two re-encryption operation for N and S attributes
    assert root.children[0].operation == 're-encryption'
    assert root.children[0].Ae == set('N')
    assert root.children[1].operation == 're-encryption'
    assert root.children[1].Ae == set('S')
    # Procedure should assign leaves to storage provider
    assert root.children[0].children[0].assignee == r.storage_provider
    assert root.children[1].children[0].assignee == r.storage_provider
    # Create a tree with only one node to test insertion of re-encryption operations at leaves
    root = Node(operation='projection', Ap=set(), Ae=set(), enc_attr=set('NP'), size=2, parent=root)
    root.relation = r
    # Insert a re-encryption of an attribute pushed down
    to_enc_dec = set('N')
    compute_assignment(
        root=root, subjects=subjects, authorizations=authorizations, to_enc_dec=to_enc_dec, relations=relations,
        avg_comp_price=3, avg_transfer_price=3, manual_assignment=manual_assignment)
    assert root.parent.operation == 're-encryption'
