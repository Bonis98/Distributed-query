# Class describing a subject with its authorization
class Subject:
    def __init__(self, name, plain_attr: set, enc_attr: set):
        self.name = name
        self.plain_attr = plain_attr
        self.enc_attr = enc_attr
