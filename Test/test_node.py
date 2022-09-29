from node import Node
from relation import Relation


def test_compute_profile():
    # Create a base relation
    r = Relation(
        storage_provider='S', attributes='NSPC', enc_costs=list('1234'), dec_costs=list('1234'), size=list('1234'))
    # Create a tree with only one node in order to test projection
    root = Node(operation='projection', Ap=set('N'), Ae=set('S'), enc_attr=set('P'), size=2)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set('N')
    assert root.ve == set('S')
    assert root.vE == set('P')
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == set()
    # create a new node in order to test selection in the form of 'a op x'
    root = Node(operation='selection', Ap=set('N'), Ae=set('S'), enc_attr=set(), size=2, select_multi_attr=False)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set('N')
    assert root.ve == set('S')
    assert root.vE == set('PC')
    assert root.ip == set('N')
    assert root.ie == set('S')
    assert root.eq == set()
    # create a new node in order to test selection in the form of a_i op a_j
    root = Node(operation='selection', Ap=set('NS'), Ae=set('PC'), enc_attr=set(), size=2, select_multi_attr=True)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    eq = set()
    eq.add(frozenset('NS'))
    eq.add(frozenset('PC'))
    assert root.vp == set('NS')
    assert root.ve == set('PC')
    assert root.vE == set()
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == eq
    # create a new node in order to test encryption
    root = Node(operation='encryption', Ap=set('NS'), Ae=set(), enc_attr=set(), size=2)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set()
    assert root.ve == set('NS')
    assert root.vE == set('PC')
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == set()
    # create a new node in order to test decryption
    root = Node(operation='decryption', Ap=set(), Ae=set("N"), enc_attr=set(), size=2)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set('N')
    assert root.ve == set()
    assert root.vE == set('SPC')
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == set()
    # create a new node in order to test re-encryption
    root = Node(operation='re-encryption', Ap=set(), Ae=set("N"), enc_attr=set(), size=2)
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set()
    assert root.ve == set('N')
    assert root.vE == set('SPC')
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == set()
    # create a new node in order to test group-by
    root = Node(operation='group-by', Ap=set("C"), Ae=set("NS"), enc_attr=set(), size=2, group_attr='C')
    # Assign base relation to the node
    root.relation = r
    root.compute_profile()
    assert root.vp == set('C')
    assert root.ve == set('NS')
    assert root.vE == set()
    assert root.ip == set('C')
    assert root.ie == set()
    assert root.eq == set()
    # create a new node with two children in order to test join
    root = Node(operation='join', Ap=set("NS"), Ae=set(), enc_attr=set(), size=2)
    Node(operation='projection', Ap=set('NP'), Ae=set(), enc_attr=set(), size=2, parent=root)
    Node(operation='projection', Ap=set('SC'), Ae=set(), enc_attr=set(), size=2, parent=root)
    # Assign base relation to nodes
    root.relation = r
    root.children[0].relation = r
    root.children[1].relation = r
    # Compute profiles of nodes
    root.children[0].compute_profile()
    root.children[1].compute_profile()
    root.compute_profile()
    eq = set()
    eq.add(frozenset('NS'))
    assert root.vp == set('NPSC')
    assert root.ve == set()
    assert root.vE == set()
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == eq
    # create a new node with two children in order to test cartesian product
    root = Node(operation='cartesian', Ap=set('NPSC'), Ae=set(), enc_attr=set(), size=2)
    Node(operation='projection', Ap=set('NP'), Ae=set(), enc_attr=set(), size=2, parent=root)
    Node(operation='projection', Ap=set('SC'), Ae=set(), enc_attr=set(), size=2, parent=root)
    # Assign base relation to nodes
    root.relation = r
    root.children[0].relation = r
    root.children[1].relation = r
    # Compute profiles of nodes
    root.children[0].compute_profile()
    root.children[1].compute_profile()
    root.compute_profile()
    assert root.vp == set('NPSC')
    assert root.ve == set()
    assert root.vE == set()
    assert root.ip == set()
    assert root.ie == set()
    assert root.eq == set()
