
# Assignment
This is a project made for the master's thesis in my cybersecurity degree. The project consists in the implementation of the algorithm proposed in **Distributed Query Execution under Access Restrictions**

<a id='install'></a>
# Installation and run
1. Clone this Repo
2. `cd` into the project root folder, and run `python3.9 -m venv env` to create a virtual env
3. Run `source env/bin/activate` to activate the virtual env
4. Run `pip install -r requirements.txt` to install all the packages needed to run the project
    - If you don't have pip installed, you can find informations [here](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#installing-pip)
5. The script has five command line arguments:
    - -p PATH, --path PATH: representing the path where to save the pdf containing the tree resulting from the computation (e.g. '../' to save the pdf in the directory containing the script folder)
    - -m ASSIGNMENT, --manual ASSIGNMENT: Manually assign node to candidate, in the form 'XYZ' to assign them to nodes in pre-order
    - -i INPUT, --input INPUT: Path from where take the input of the algorithm
    - -v, --verbose: Enables verbose logging
    - -d, --debug: Enables debugging loggin

[back](#top)

<a id='Input'></a>
# Input data to algorithm
Inputs to the algorithm are given by four different CSV files:
- [relations.cvs](CSV_data/relations.csv)
- [tree.cvs](CSV_data/tree.csv)
- [subjects.cvs](CSV_data/subjects.csv)
- [authorizations.cvs](CSV_data/authorizations.csv)

Folder [CSV_data](CSV_data) contains an example of that files

<a id='relations'></a>
### relations.csv
This is the file modeling the base relations of the query, structured as follows:
- **provider**: Storage provider storing the relationship
- **attributes**: Attributes of the relationship
- **enc_costs**: list of encryption costs of attributes in the relationship
- **dec_costs**: list of decryption costs of attributes in the relationship
- **size**: list of attributes sizes (used to compute computational cost of node)
- **node_id**: id of the leaf node in the tree to which associate the base relation (see [nodes.csv](#nodescsv))

Parsing of [relations.csv](CSV_data/relations.csv) produces the following two base relations:
1. **relation 1**(NPC) assigned to storage provider **F**
    - N has an encryption cost of 1, a decryption cost of 4 and a size of 7
    - P has an encryption cost of 2, a decryption cost of 5 and a size of 8
    - C has an encryption cost of 3, a decryption cost of 6 and a size of 9
1. **relation 2**(SJI) assigned to storage provider **C**
    - S has an encryption cost of 1, a decryption cost of 4 and a size of 7
    - J has an encryption cost of 2, a decryption cost of 5 and a size of 8
    - I has an encryption cost of 3, a decryption cost of 6 and a size of 9

<a id='nodes'></a>
### tree.csv
This is the file modeling the query tree plan, structured as follows:
- **ID**: Used to associate a relationship with a leaf node
- **operation**: Operation of the query associated with the node
  - Projection
  - Selection
  - Cartesian
    - Cartesian product requires to put manually attributes in Ap, Ae and enc_attr taken from children
  - Join
  - Group-by
  - Encryption
  - Decryption
  - Re-encryption
- **Ap**: Set of attributes that need to be in plaintext to evaluate the operation associated with the node
- **Ae**: Set of attributes that need to be re-encrypted to evaluate the operation associated with the node
- **enc_attr**: Set of attributes encrypted in storage (default for base relations)
- **size**: size of the node (used to compute computational cost of node)
- **print_label**: label of the node to print when tree is exported 
- **group_attr**: if the operation associated with the node is a *group-by*, this is the set of attributes on which the group-by clause is evaluated
- **parent**: parent node of current node, used to build the tree

Parsing of [tree.csv](CSV_data/tree.csv) produces the following tree:

<p align="center">
<img src="https://user-images.githubusercontent.com/25297357/191472462-4ed9ed1f-9301-4b5f-8e05-6d27d1f111db.png" alt="nodes" width="200" align="center"/>
</p>

<a id='subjects'></a>
### subjects.csv
This is the file modeling the subjects involved in query computation with its authorizations, structured as follows:
- **subject**: Name of the subject
- **comp_price**: computational price of the subject
- **transfer_price**: transfer price of the subject

Parsing of [subjects.csv](CSV_data/subjects.csv) produces the following subjects:
- U with computational price 1 and transfer price 1
- X with computational price 2 and transfer price 2
- Y with computational price 3 and transfer price 3
- Z with computational price 4 and transfer price 4
- F with computational price 5 and transfer price 6
- C with computational price 6 and transfer price 7

<a id='authorizations'></a>
### authorizations.csv
This is the file modeling the authorizations involved in query computation, structured as follows:
- **subject**: Name of the subject (already specified in [subjects.csv](CSV_data/subjects.csv))
- **plain**: Attributes for which the subject is authorized to view in plaintext form
- **enc**: Attributes for which the subject is authorized to view in encrypted form

Parsing of [authorizations.csv](CSV_data/authorizations.csv) produces the following authorizations:
- [NCPSJI,-]&#8594;U
- [PC,NSJI]&#8594;X
- [DPJI,CNS]&#8594;Y
- [NCS,PJI]&#8594;Z
- [-,NDPCJI]&#8594;F
- [-,NCSJI]&#8594;C

[back](#top)
