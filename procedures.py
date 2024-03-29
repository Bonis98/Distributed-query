import itertools
import logging
import math

from anytree import PostOrderIter, PreOrderIter

from node import Node


def compute_cost(root, subjects: dict):
    logging.info('Computing costs of subjects...')
    for node in PostOrderIter(root):
        node.comp_cost = dict()
        logging.debug('Processing costs on node %s', node.name)
        for subject in subjects:
            # Node cost
            node.comp_cost[subject] = (subjects[subject]['comp_price'] * node.size)
            # Children costs
            for child in node.children:
                node.comp_cost[subject] = node.comp_cost[subject] + child.comp_cost[subject]


def identify_candidates(root: Node, subjects: dict, authorizations: dict, global_Ap: set):
    for node in PostOrderIter(root):
        logging.info('Identifying candidate on node %s', node.name)
        if node.is_leaf:
            # Initializes profile of base projections (overriding them with encryption of all possible attributes)
            node.vp = set(global_Ap).difference(node.relation.enc_attr).intersection(node.attributes)
            node.ve = set(node.relation.plain_attr).difference(global_Ap).intersection(node.attributes)
            node.vE = set(node.relation.enc_attr).intersection(node.attributes)
            node.ip = set()
            node.ie = set()
            node.eq = set()
            # Candidates are any subject
            node.candidates = list(subjects.keys())
            # No need to initialize totap and totae (already empty)
        else:
            # Ap and Ae already initialized
            # Attributes are already encrypted
            node.compute_profile()
            for child in node.children:
                node.totAp = node.Ap.union(child.totAp)
                node.totAe = node.Ae.union(child.totAe)
            # Initialize candidates to empty
            node.candidates = list()
            # Monotonicity property
            cand = list(subjects.keys())
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
                if __is_authorized(authorizations[subject], node):
                    node.candidates.append(subject)
            logging.debug('Final candidate(s) for %s: %s', node.name, node.candidates)
            # If node has no candidates, print error and stop the computation
            if len(node.candidates) == 0:
                print('No candidates available for node ' + node.name)
                exit()


def compute_assignment(
        root: Node, subjects: dict, authorizations: dict, relations: list,
        avg_comp_price: float, avg_transfer_price: float, manual_assignment=None):
    to_enc_dec = set()
    for node in PreOrderIter(root):
        logging.info('Computing assignee for node %s', node.name)
        s_min = None
        min_cost = math.inf
        if node.is_leaf:
            # Assign node to the storage provider
            node.assignee = node.relation.storage_provider
            # Base relation of the node contains attributes to be re-encrypted
            if len(to_enc_dec.intersection(set(node.relation.enc_attr))):
                att = to_enc_dec.intersection(set(node.relation.enc_attr))
                for cand in subjects.keys():
                    # Candidates are already sorted by comp+transfer price
                    re_enc = att.intersection(set(authorizations[cand]['plain']))
                    if len(re_enc) and __is_authorized(authorizations[cand], node):
                        # Insert re-encryption node for 'dec' as parent of current node
                        logging.debug('Inserting a re-encryption node for attribute(s) %s', re_enc)
                        n = Node(
                            operation='re-encryption', Ap=set(), Ae=re_enc, As=set(), cryptographic=True,
                            print_label='Re-encrypt ' + str(re_enc), parent=node.parent, children={node})
                        n.assignee = cand
                        n.compute_profile()
                        # This line in the paper was one indentation back
                        att = att.difference(re_enc)
                        to_enc_dec = to_enc_dec.difference(re_enc)
                if len(att):
                    print('Error: %s attributes cannot be re-encrypted' % att)
                    exit()
        elif not node.cryptographic:
            for cand in node.candidates:
                # Calculate transfer cost of relation
                if cand != node.parent.assignee:
                    cost = node.size * subjects[cand]['transfer_price']
                else:
                    cost = 0
                cost += node.comp_cost[cand]  # Calculate computational cost
                for attr in node.totAp.union(node.totAe).intersection(set(authorizations[cand]['plain'])):
                    for rel in relations:  # S decrypts the attribute
                        if attr in rel.enc_attr:
                            cost += int(rel.dec_costs[rel.attr.index(attr)]) * subjects[cand]['comp_price']
                for attr in node.totAe.difference(set(authorizations[cand]['plain'])):
                    for rel in relations:  # Need to delegate re-encryption of attribute
                        if attr in rel.enc_attr:
                            index = rel.attr.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) \
                                    * avg_comp_price + int(rel.size[index]) \
                                    * (avg_transfer_price + int(subjects[cand]['transfer_price']))
                enc = node.ve.union(node.ie)
                for child in node.children:
                    enc = enc.union(child.ve).union(node.ie)
                for attr in enc.intersection(set(authorizations[cand]['enc'])):
                    for rel in relations:  # Need to delegate encryption of attribute
                        if attr in rel.plain_attr:
                            index = rel.attr.index(attr)
                            cost += int(rel.enc_costs[index]) \
                                    * subjects[rel.storage_provider]['comp_price']
                            # Decryption cost of attributes performed by User to see query result
                            cost += int(rel.dec_costs[rel.attr.index(attr)]) * subjects['U']['comp_price']
                for attr in to_enc_dec.intersection(authorizations[cand]['plain']):  # S can re-encrypt attribute
                    for rel in relations:
                        if attr in rel.enc_attr:
                            index = rel.attr.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) \
                                    * subjects[cand]['comp_price']
                if cost < min_cost:
                    min_cost = cost
                    s_min = cand
            node.assignee = s_min  # Select subject with minimum cost for evaluate current node
            # Manual assignment of candidates, used only for debug
            if manual_assignment is not None:
                node.assignee = manual_assignment.pop(0)
            # Insert re-encryption node for to_enc_dec attributes pushed down
            if len(to_enc_dec.intersection(set(authorizations[node.assignee]['plain']))):
                Ae = to_enc_dec.intersection(set(authorizations[node.assignee]['plain']))
                logging.debug('Inserting a re-encryption node for attribute(s) %s', Ae)
                n = Node(
                    operation='re-encryption', Ap=set(), Ae=Ae, As=set(), cryptographic=True,
                    print_label='Re-encrypt ' + str(Ae), parent=node.parent, children={node})
                n.assignee = node.assignee
                n.compute_profile()
                to_enc_dec = to_enc_dec.difference(set(authorizations[node.assignee]['plain']))
            to_enc_dec = to_enc_dec.union(node.Ae.difference(set(authorizations[node.assignee]['plain'])))
            # Insert re-encryption node for attributes that need to be re-encrypted
            if len(node.Ae.intersection(set(authorizations[node.assignee]['plain']))):
                # Need to search correct path in the tree
                for child in node.children:
                    re_enc = node.Ae.intersection(set(authorizations[node.assignee]['plain'])).difference(child.Ap)
                    for leaf in child.leaves:
                        path_attr = leaf.Ae.union(leaf.As).intersection(re_enc)
                        for descendant in node.descendants:
                            path_attr = path_attr.difference(descendant.Ae)
                            if not len(path_attr):
                                break
                        if len(path_attr):
                            logging.debug('Inserting a re-encryption node for attribute(s) %s', path_attr)
                            child = Node(
                                operation='re-encryption', Ap=set(), Ae=path_attr, As=set(), cryptographic=True,
                                print_label='Re-encrypt ' + str(path_attr), parent=node, children={child})
                            child.assignee = node.assignee
                            child.compute_profile()
        logging.debug('Assignee for %s: %s', node.name, node.assignee)


def insert_encryption(authorizations, relations, root, subjects):
    # Recompute profile of leaves after override
    for node in PostOrderIter(root, filter_=lambda n: n.is_leaf):
        node.compute_profile()
    encrypted = set()
    # Insert and push down encryption
    for node in PostOrderIter(root, filter_=lambda n: not n.is_leaf and not n.cryptographic):
        for rel in relations:
            attr = set(node.ve).union(node.ie)
            for child in node.children:
                attr = attr.union(child.ve).union(child.ie)
            attr = attr.intersection(rel.plain_attr)
            encrypt = set(authorizations[node.assignee]['enc']).intersection(attr).difference(encrypted)
            for attr in encrypt:
                # Insert encryption
                for leaf in node.leaves:
                    if attr in leaf.attributes:
                        new_node = Node(
                            operation='encryption', Ap=attr,
                            print_label='Encrypt ' + str(attr), cryptographic=True, parent=leaf.parent,
                            children={leaf})
                        new_node.assignee = leaf.assignee
                        encrypted = encrypted.union(encrypt)
    # Recompute profile of nodes after inserting encryption
    for node in PostOrderIter(root):
        node.compute_profile()


def extend_plan(root: Node, authorizations: dict):
    logging.info('Extending plan with encryption/decryption operations...')
    for node in PostOrderIter(root):
        logging.debug('Extending plan for node %s', node.name)
        if node.is_root:
            decrypt = set()
            for child in node.children:
                decrypt = decrypt.union(child.ve, child.vE)
            if len(decrypt):
                logging.debug('Inserting a decryption node for attribute(s) %s assigned to U', decrypt)
                new_node = Node(
                    operation='decryption', Ap=set(), Ae=decrypt, As=set(),
                    print_label='Decrypt ' + str(decrypt), cryptographic=True, parent=node, children={node.children[0]})
                new_node.assignee = 'U'
        elif len(node.children) and not node.cryptographic:
            for child in node.children:
                dec = node.Ap.intersection(child.ve.union(child.vE))
                if len(dec):
                    logging.debug('Inserting a decryption node for attribute(s) %s', dec)
                    new_node = Node(
                        operation='decryption', Ap=set(), Ae=dec, As=set(),
                        print_label='Decrypt ' + str(dec), cryptographic=True, parent=node, children={child})
                    new_node.compute_profile()
                    new_node.assignee = node.assignee
        if not node.is_root and not node.parent.cryptographic:
            enc = node.vp.intersection(authorizations[node.parent.assignee]['enc'])
            if len(enc):
                new_node = Node(
                    operation='encryption', Ap=enc,
                    print_label='Encrypt ' + str(enc), cryptographic=True, parent=node.parent, children={node})
                new_node.compute_profile()
                new_node.assignee = node.assignee


def comp_size(root: Node, relations: list):
    logging.info("Computing size of nodes...")
    for node in PostOrderIter(root):
        logging.debug("Computing size of node %s", node.name)
        vp = set()
        ve = set()
        vE = set()
        if not node.is_leaf:
            for child in node.children:
                vp = vp.union(child.vp)
                ve = ve.union(child.ve)
                vE = vE.union(child.vE)
        else:
            vp = node.vp
            ve = node.ve
            vE = node.vE
        for relation in relations:
            for attr in itertools.chain(vp, ve, vE):
                if attr in relation.attr:
                    index = relation.attr.index(attr)
                    node.size += int(relation.size[index])


def __is_authorized(authorization, node: Node):
    # Create a list containing current node and its children
    nodes = list()
    nodes.append(node)
    for child in node.children:
        nodes.append(child)
    for node in nodes:
        # Authorized for plaintext
        if not node.vp.union(node.ip).issubset(set(authorization['plain'])):
            return False
        # Authorized for encrypted
        if not node.ve.union(node.vE, node.ie).issubset(set(authorization['enc']).union(set(authorization['plain']))):
            return False
        # Uniform visibility
        for eq in node.eq:
            if not eq.issubset(set(authorization['plain'])):
                if not eq.issubset(set(authorization['enc'])):
                    return False
    return True
