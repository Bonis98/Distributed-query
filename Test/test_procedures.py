import io

import pandas as pd

from node import Node
from procedures import compute_cost


def test_compute_cost():
    # Create a tree with only one node
    root = Node(operation="selection", Ap=set(), Ae=set(), enc_attr=set(), size=2)
    # Create two subjects with different computational price
    csv_data = io.StringIO("subject,comp_price\nU,1\nX,2")
    df = pd.read_csv(csv_data)
    subjects = df.set_index('subject').T.to_dict('dict')
    compute_cost(root, subjects)
    node = root
    # Check len and value of computational cost computed
    assert len(node.comp_cost) == len(df.index)
    assert node.comp_cost['U'] == df['comp_price'].values[0] * 3
    assert node.comp_cost['X'] == df['comp_price'].values[1] * 3
    # Add a child node
    Node(operation="projection", Ap=set(), Ae=set(), enc_attr=set(), size=2, parent=root)
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
    Node(operation="join", Ap=set(), Ae=set(), enc_attr=set(), size=2, parent=root)
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
    assert node.comp_cost['U'] == df['comp_price'].values[0]\
           * 3\
           + node.children[0].comp_cost['U']\
           + node.children[1].comp_cost['U']
    assert node.comp_cost['X'] == df['comp_price'].values[1]\
           * 3\
           + node.children[0].comp_cost['X']\
           + node.children[1].comp_cost['X']
