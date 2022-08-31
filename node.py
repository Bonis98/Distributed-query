class Node:
    permitted_ops = ['projection', 'selection', 'cartesian', 'join',
                     'group by', 'encryption', 'decryption', 're-encryption']

    def __init__(self, operation, attributes):
        if operation not in self.permitted_ops:
            raise ValueError("results: status must be one of %r." % self.permitted_ops)
        self.operation = operation
        self.attributes = attributes
