# Class describing a subject with its authorizations
class Authorization:
    def __init__(self, subject, plain_attr: set, enc_attr: set):
        self.subject = subject
        self.plain_attr = set(plain_attr)
        self.enc_attr = set(enc_attr)
