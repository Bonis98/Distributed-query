class Relation:
    def __init__(self, storage_provider, attributes: list, enc_costs: list, dec_costs: list, size: list):
        self.storage_provider = storage_provider
        if not (len(attributes) == len(enc_costs) == len(dec_costs) == len(size)):
            raise ValueError('Relation: attributes, enc_costs dec_costs and size must have the same length')
        self.attributes = list(attributes)
        self.enc_costs = list(enc_costs)
        self.dec_costs = list(dec_costs)
        self.size = list(size)
