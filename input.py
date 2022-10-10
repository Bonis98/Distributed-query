import pandas as pd

from node import Node
from relation import Relation


def read_input(input_path):
    nodes = read_tree(input_path)
    relations = read_relations(input_path, nodes)
    subjects, avg_comp_price, avg_transfer_price = read_subjects(input_path)
    authorizations = read_authorizations(input_path)
    return nodes[0], relations, subjects, authorizations, avg_comp_price, avg_transfer_price


def read_tree(input_path):
    nodes = list()
    df = pd.read_csv(input_path + 'tree.csv')
    df['parent'] = df['parent'].fillna(value=0)
    df = df.fillna(value='')
    df = df.astype({'ID': 'int', 'size': 'int', 'parent': 'int'})
    df = df.astype({'Ap': 'str', 'Ae': 'str', 'enc_attr': 'str'})
    for idx, row in df.iterrows():
        multi_attr = False
        if row['operation'] == 'selection':
            if len(row['Ap']) > 1 or len(row['Ae']) > 1 or len(row['enc_attr']) > 1:
                multi_attr = True
        if not idx:
            node = Node(
                operation=row['operation'], Ap=row['Ap'], Ae=row['Ae'], enc_attr=row['enc_attr'], size=row['size'],
                print_label=row['print_label'], group_attr=row['group_attr'], select_multi_attr=multi_attr)
        else:
            node = Node(
                operation=row['operation'], Ap=row['Ap'], Ae=row['Ae'], enc_attr=row['enc_attr'],
                size=row['size'], print_label=row['print_label'], group_attr=row['group_attr'],
                select_multi_attr=multi_attr, parent=nodes[row['parent'] - 1])
        nodes.append(node)
    return nodes


def read_relations(input_path, nodes: list):
    relations = list()
    df = pd.read_csv(input_path + 'relations.csv')
    df = df.astype('str')
    df = df.astype({'node_id': int})
    for idx, row in df.iterrows():
        relation = Relation(
            storage_provider=row['provider'], attributes=row['attributes'],
            enc_costs=row['enc_costs'], dec_costs=row['dec_costs'], size=row['size'])
        relations.append(relation)
        nodes[row['node_id'] - 1].relation = relation
    return relations


def read_subjects(input_path):
    df = pd.read_csv(input_path + 'subjects.csv')
    if df.isnull().values.any():
        raise ValueError("Input: Subjects dataframe can't contain NaN values")
    df['sum'] = df['comp_price'] + df['transfer_price']
    df = df.sort_values(by=['sum'])
    df = df.drop(columns=['sum'])
    subjects = df.set_index('subject').T.to_dict('dict')
    avg_comp_price = df['comp_price'].mean()
    avg_transfer_price = df['transfer_price'].mean()
    return subjects, avg_comp_price, avg_transfer_price


def read_authorizations(input_path):
    df = pd.read_csv(input_path + 'authorizations.csv')
    df = df.fillna(value='')
    return df.set_index('subject').T.to_dict('dict')
