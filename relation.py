class Relation:
    def __init__(self, name, storage_provider, primary_key: list, plain_attr: list,
                 enc_attr: list, attr: list, enc_costs: str, dec_costs: str, size: str):
        self.name = name
        self.storage_provider = storage_provider
        if not (primary_key in plain_attr or primary_key in enc_attr):
            raise ValueError('Relation: primary key is not valid')
        self.primary_key = list(primary_key)
        enc_costs = enc_costs.split(';')
        dec_costs = dec_costs.split(';')
        size = size.split(';')
        if not (len(attr) == len(enc_costs) == len(dec_costs) == len(size)):
            raise ValueError('Relation: attributes, enc_costs dec_costs and size must have the same length')
        self.plain_attr = list(plain_attr)
        self.enc_attr = list(enc_attr)
        self.attr = list(attr)
        self.enc_costs = enc_costs
        self.dec_costs = dec_costs
        self.size = size
