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
            node.comp_cost[subject] = (subjects[subject]['comp_price'] * node.get_op_cost())
            # Children costs
            for child in node.children:
                node.comp_cost[subject] = node.comp_cost[subject] + child.comp_cost[subject]


def identify_candidates(root: Node, subjects: dict, authorizations: dict):
    logging.info('Identifying candidates for each node...')
    for node in PostOrderIter(root):
        logging.debug('Identifying candidate on node %s', node.name)
        if node.is_leaf:
            # Initializes profile to all empty except for vE that is set to all relation's attributes
            node.compute_profile()
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
                # Authorized for current node
                if __is_authorized(authorizations[subject], node=node):
                    # Authorized for first child of current node
                    if __is_authorized(authorizations[subject], node=node.children[0]):
                        # If node has two children verify if it is authorized for the second
                        if len(node.children) == 2:
                            # Authorized for second child (if present)
                            if __is_authorized(authorizations[subject], node=node.children[1]):
                                node.candidates.append(subject)
                        # If node has one child, then subject is authorized
                        else:
                            node.candidates.append(subject)
            logging.debug('Final candidate(s) for %s: %s', node.name, node.candidates)
            # If node has no candidates, print error and stop the computation
            if len(node.candidates) == 0:
                print('No candidates available for node ' + node.name)
                exit()


def compute_assignment(
        root: Node, subjects: dict, authorizations: dict, to_enc_dec: set, relations: list,
        avg_comp_price: float, avg_transfer_price: float, manual_assignment=None):
    logging.info('Computing assignee for each node...')
    for node in PreOrderIter(root):
        logging.debug('Computing assignee for node %s', node.name)
        s_min = None
        min_cost = math.inf
        if node.is_leaf:
            # Assign node to the storage provider
            node.assignee = node.relation.storage_provider
            # Base relation of the node contains attributes to be re-encrypted
            if len(to_enc_dec.intersection(set(node.relation.attributes))):
                att = to_enc_dec.intersection(set(node.relation.attributes))
                for cand in subjects.keys():
                    # Candidates are already sorted by comp+transfer price
                    dec = att.intersection(set(authorizations[cand]['plain']))
                    if len(dec) and set(node.relation.attributes) \
                            .issubset(set(authorizations[cand]['plain']).union(set(authorizations[cand]['enc']))):
                        # Insert re-encryption node for 'dec' as parent of current node
                        logging.debug('Inserting a re-encryption node for attribute(s) %s', dec)
                        n = Node(
                            operation='re-encryption', Ap=set(), Ae=dec, enc_attr=set(), cryptographic=True,
                            print_label='Re-encrypt ' + str(dec), parent=node.parent, children={node})
                        n.assignee = cand
                        # This line in the paper was one indentation back
                        att = att.difference(dec)
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
                        if attr in rel.attributes:
                            cost += int(rel.dec_costs[rel.attributes.index(attr)]) * subjects[cand]['comp_price']
                for attr in node.totAe.difference(set(authorizations[cand]['plain'])):
                    for rel in relations:  # Need to delegate re-encryption of attribute
                        if attr in rel.attributes:
                            index = rel.attributes.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) \
                                    * avg_comp_price + int(rel.size[index]) \
                                    * (avg_transfer_price + int(subjects[cand]['transfer_price']))
                for attr in to_enc_dec.intersection(authorizations[cand]['plain']):  # S can re-encrypt attribute
                    for rel in relations:
                        if attr in rel.attributes:
                            index = rel.attributes.index(attr)
                            cost += (int(rel.dec_costs[index]) + int(rel.enc_costs[index])) \
                                    * subjects[cand]['comp_price']
                if cost < min_cost:
                    min_cost = cost
                    s_min = cand
            node.assignee = s_min  # Select subject with minimum cost for evaluate current node
            # Manual assignment, used only for debug
            if manual_assignment is not None:
                node.assignee = manual_assignment.pop(0)
            # Insert re-encryption node for to_enc_dec attributes pushed down
            if len(to_enc_dec.intersection(set(authorizations[node.assignee]['plain']))):
                Ae = to_enc_dec.intersection(set(authorizations[node.assignee]['plain']))
                logging.debug('Inserting a re-encryption node for attribute(s) %s', Ae)
                n = Node(
                    operation='re-encryption', Ap=set(), Ae=Ae, enc_attr=set(), cryptographic=True,
                    print_label='Re-encrypt ' + str(Ae), parent=node.parent, children={node})
                n.assignee = node.assignee
                to_enc_dec = to_enc_dec.difference(set(authorizations[node.assignee]['plain']))
            to_enc_dec = to_enc_dec.union(node.Ae.difference(set(authorizations[node.assignee]['plain'])))
            # Insert re-encryption node for attributes that need to be re-encrypted
            if len(node.Ae.intersection(set(authorizations[node.assignee]['plain']))):
                # Need to search correct path in the tree
                for child in node.children:
                    re_enc = node.Ae.intersection(set(authorizations[node.assignee]['plain']))
                    # Insertion of encryption is not mentioned in the paper
                    enc = re_enc.intersection(child.Ap)
                    re_enc = re_enc.difference(child.Ap)
                    for leaf in child.leaves:
                        path_attr = leaf.Ae.union(leaf.enc_attr).intersection(re_enc)
                        for descendant in node.descendants:
                            path_attr = path_attr.difference(descendant.Ae)
                            if not len(path_attr):
                                break
                        if len(path_attr):
                            logging.debug('Inserting a re-encryption node for attribute(s) %s', path_attr)
                            child = Node(
                                operation='re-encryption', Ap=set(), Ae=path_attr, enc_attr=set(), cryptographic=True,
                                print_label='Re-encrypt ' + str(path_attr), parent=node, children={child})
                            child.assignee = node.assignee
                        path_attr = leaf.Ae.union(leaf.enc_attr).intersection(enc)
                        if len(path_attr):
                            logging.debug('Inserting an encryption node for attribute(s) %s', path_attr)
                            child = Node(
                                operation='encryption', Ap=path_attr, Ae=set(), enc_attr=set(), cryptographic=True,
                                print_label='Encrypt ' + str(path_attr), parent=node, children={child})
                            child.assignee = node.assignee
                            # After inserting a cryptographic operation, recompute candidates
                            identify_candidates(child.root, subjects, authorizations)
        logging.debug('Assignee for %s: %s', node.name, node.assignee)


def extend_plan(root: Node, subjects: dict, authorizations: dict):
    logging.info('Extending plan with encryption/decryption operations...')
    for node in PostOrderIter(root):
        logging.debug('Extending plan for node %s', node.name)
        if node.is_root:
            decrypt = set()
            for child in node.children:
                decrypt = decrypt.union(child.ve, child.vE)
            if len(decrypt):
                logging.debug('Inserting a decryption node for attribute(s) %s assigned to U', decrypt)
                n = Node(
                    operation='decryption', Ap=set(), Ae=decrypt, enc_attr=set(),
                    print_label='Decrypt ' + str(decrypt), cryptographic=True, parent=node, children={node.children[0]})
                n.assignee = 'U'
        else:
            for child in node.children:
                dec = node.Ap.intersection(child.ve.union(child.vE)).difference(child.vp)
                if len(dec):
                    logging.debug('Inserting a decryption node for attribute(s) %s', dec)
                    n = Node(
                        operation='decryption', Ap=set(), Ae=dec, enc_attr=set(),
                        print_label='Decrypt ' + str(dec), cryptographic=True, parent=node, children={child})
                    # After inserting a cryptographic operation, recompute candidates
                    identify_candidates(n.root, subjects, authorizations)
                    n.assignee = node.assignee
            node.compute_profile()
            enc = node.vp.intersection(authorizations[node.parent.assignee]['enc'])
            if len(enc):
                logging.debug('Inserting an encryption node for attribute(s) %s', enc)
                n = Node(
                    operation='encryption', Ap=enc, Ae=set(), enc_attr=set(),
                    print_label='Encrypt ' + str(enc), cryptographic=True, parent=node.parent, children={node})
                n.compute_profile()
                # Candidates need to be re-identified after inserting an encryption operation
                identify_candidates(n.root, subjects, authorizations)
                n.assignee = node.assignee


def __is_authorized(authorization, node: Node):
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
