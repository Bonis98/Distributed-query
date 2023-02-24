import pandas as pd
import random
import sys
import os

df = pd.read_csv(sys.argv[1] + 'relations.csv')
df = df.astype('str')
attributes = ''
authorizations = dict()
for idx, row in df.iterrows():
    attributes += row['attributes']
    authorizations[row['provider']] = '', ''.join(sorted(row['attributes']))
attributes = list(attributes)
authorizations['U'] = ''.join(sorted(attributes)), ''
subjects = list('LMNOPQRST')
for subject in subjects:
    random.shuffle(attributes)
    n1 = random.randint(0, len(attributes))
    n2 = random.randint(n1, len(attributes))
    if random.randint(0, 1):
        authorizations[subject] = ''.join(sorted(attributes[0:n1])), ''.join(sorted(attributes[n1:n2]))
    else:
        authorizations[subject] = ''.join(sorted(attributes[n1:n2])), ''.join(sorted(attributes[0:n1]))
df = df.from_dict(authorizations, orient='index', columns=['plain', 'enc'])
df = df.reset_index()
df = df.rename(columns={"index": "subject"})
print(df)
df.to_csv(path_or_buf=sys.argv[1] + 'authorizations.csv', index=False)
subjects = dict.fromkeys(authorizations.keys())
for subject in subjects:
    comp_prices = str(random.randint(1, 9))
    transfer_prices = str(random.randint(1, 9))
    subjects[subject] = comp_prices, transfer_prices
df = df.from_dict(subjects, orient='index', columns=['comp_price', 'transfer_price'])
df = df.reset_index()
df = df.rename(columns={"index": "subject"})
print(df)
df.to_csv(path_or_buf=sys.argv[1] + 'subjects.csv', index=False)
try:
    os.remove(sys.argv[1] + 'Plan.pdf')
    os.remove(sys.argv[1] + 'Tree.pdf')
except OSError:
    pass
