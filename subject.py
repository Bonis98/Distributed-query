# Class describing a subject with its authorizations
class Subject:
    def __init__(self, name, plain_attr: set, enc_attr: set, comp_price: int):
        self.name = name
        self.plain_attr = plain_attr
        self.enc_attr = enc_attr
        self.comp_price = comp_price
