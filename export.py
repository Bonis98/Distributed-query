from anytree.exporter import DotExporter

from node import Node


def export_tree(filename, root, dot=False):
    # Dot parameter can be used to export a dot file instead of a picture
    if dot:
        DotExporter(root, nodeattrfunc=node_attr, edgeattrfunc=lambda *args: 'dir=back').to_dotfile(filename)
    else:
        DotExporter(root, nodeattrfunc=node_attr, edgeattrfunc=lambda *args: 'dir=back').to_picture(filename)


def node_attr(node: Node):
    # If operation is a cryptographic operation draw an ellipse box
    if node.re_encryption or node.operation == 'decryption' or node.operation == 'encryption':
        label = 'label=<'
        for attr in node.Ae:
            label += attr
        label += '<BR/>Assignee:&nbsp;<B>' + node.assignee + '</B>'
        label += '>'
        # Re-encryption is half greyed out
        if node.re_encryption:
            label += 'style=filled, fillcolor=\"white;0.5:lightgrey\", gradientangle=90'
        # Encryption is totally greyed out
        elif node.operation == 'encryption':
            label += 'style=filled, fillcolor=\"lightgrey\"'
    elif node.operation == 'query':
        label = 'label=<User formulating the query>, shape=box'
    # All the other nodes goes in a normal circle, with candidates and assignee in bold
    else:
        label = node.name
        label = label.replace('>', '&gt;').replace('<', '&lt;')
        label = 'label=<<table border="1" cellborder="1"><tr><td border="0" colspan="3">' + label
        label = label.replace('Selection ', '&sigma;<sub>')
        label = label.replace('Group-by ', '&gamma;<sub>')
        label = label.replace('Join ', '⋈<sub>')
        label = label.replace('Projection ', '&pi;<sub>')
        if label.find('<sub>') != -1:
            label += '</sub>'
        label += '</td>'
        label += '<td>'
        # Print profile
        for attr in node.vp:
            label += attr
        # If there are no attributes print a space
        if not node.vp:
            label += ' '
        label += '</td><td bgcolor="lightgrey">'
        for attr in node.ve:
            label += attr
        if not node.ve:
            label += ' '
        label += '</td><td bgcolor="lightgrey">'
        for attr in node.vE:
            label += attr
        if not node.vE:
            label += ' '
        label += '</td></tr><tr>'
        label += '<td border="0" colspan="3">'
        # Print candidates
        if not node.is_leaf:
            label += 'Candidates: <B>'
            for cand in node.candidates:
                label += cand
            label += '</B>'
        # Print a space in order to preserve row height
        else:
            label += ' '
        label += '</td>'
        label += '<td>'
        for attr in node.ip:
            label += attr
        if not node.ip:
            label += ' '
        label += '</td><td bgcolor="lightgrey">'
        for attr in node.ie:
            label += attr
        if not node.ie:
            label += ' '
        label += '</td></tr>'
        label += '<tr><td border="0" colspan="3">Assignee: <B>' + node.assignee + '</B></td><td>'
        # eq sets need to be printed with ; in order to separate them
        for collection in node.eq:
            for attr in collection:
                label += attr
            label += ';'
        label += '</td></tr></table>>'
        label += 'shape=plain'
        if not node.eq:
            label += ' '
    return label
