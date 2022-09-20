import pandas as pd

from node import Node, Relation


def read_input():
    nodes = read_tree()
    relations = read_relations(nodes)
    subjects, avg_comp_price, avg_transfer_price = read_subjects()

    return nodes[0], relations, subjects, avg_comp_price, avg_transfer_price


def read_tree():
    nodes = list()
    df = pd.read_csv('CSV_data/nodes.csv')
    df['parent'] = df['parent'].fillna(value=0)
    df = df.fillna(value='')
    df = df.astype({'ID': 'int', 'size': 'int', 'parent': 'int'})
    df = df.astype({'Ap': 'str', 'Ae': 'str', 'enc_attr': 'str'})
    for idx, row in df.iterrows():
        if not idx:
            node = Node(
                operation=row['operation'], Ap=row['Ap'], Ae=row['Ae'], enc_attr=row['enc_attr'], size=row['size'],
                print_label=row['print_label'], group_attr=row['group_attr'])
        else:
            node = Node(
                operation=row['operation'], Ap=row['Ap'], Ae=row['Ae'], enc_attr=row['enc_attr'],
                size=row['size'],
                print_label=row['print_label'], group_attr=row['group_attr'], parent=nodes[row['parent'] - 1])
        nodes.append(node)
    return nodes


def read_relations(nodes: list()):
    relations = list()
    df = pd.read_csv('CSV_data/relations.csv')
    df = df.astype('str')
    df = df.astype({'node_id': int})
    for idx, row in df.iterrows():
        relation = Relation(
            storage_provider=row['provider'], attributes=row['attributes'],
            enc_costs=row['enc_costs'], dec_costs=row['dec_costs'], size=row['size'])
        relations.append(relation)
        nodes[row['node_id'] - 1].relation = relation
    return relations


def read_subjects():
    df = pd.read_csv('CSV_data/subjects.csv')
    df = df.fillna(value='')
    df['sum'] = df['comp_price'] + df['transfer_price']
    df = df.sort_values(by=['sum'])
    df = df.drop(columns=['sum'])
    subjects = df.set_index('subject').T.to_dict('dict')
    avg_comp_price = df['comp_price'].mean()
    avg_transfer_price = df['transfer_price'].mean()
    return subjects, avg_comp_price, avg_transfer_price