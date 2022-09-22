# Class describing a subject with its authorizations
class Subject:
    def __init__(self, name, plain_attr: set, enc_attr: set):
        self.name = name
        self.plain_attr = set(plain_attr)
        self.enc_attr = set(enc_attr)
