import logging

from anytree.exporter import DotExporter

from node import Node


def export_tree(filename, root, dot=False):
    if 'Plan.pdf' in filename:
        logging.info('Exporting query plan in a PDF file placed in ' + filename)
    else:
        logging.info('Exporting final query plan in a PDF file placed in ' + filename)
    # Dot parameter can be used to export a dot file instead of a picture
    if dot:
        DotExporter(root, nodeattrfunc=node_attr, edgeattrfunc=lambda *args: 'dir=back').to_dotfile(filename)
    else:
        DotExporter(root, nodeattrfunc=node_attr, edgeattrfunc=lambda *args: 'dir=back').to_picture(filename)


def node_attr(node: Node):
    # If operation is a cryptographic operation draw an ellipse box
    if node.cryptographic:
        label = 'label=<'
        for attr in node.Ae:
            label += attr
        if not len(node.Ae):
            for attr in node.Ap:
                label += attr
        label += '<BR/>Assignee:&nbsp;<B>' + node.assignee + '</B>'
        label += '>'
        # Re-encryption is half greyed out
        if node.operation == 're-encryption':
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
        label = label.replace('Cartesian', '&times;')
        if label.find('<sub>') != -1:
            label += '</sub>'
        label += '</td>'
        if len(node.vp) or len(node.ve) or len(node.vE) or len(node.ip) or len(node.ie) or len(node.eq):
            # Print profile
            label += '<td>'
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
            label += '</td>'
        label += '</tr><tr>'
        label += '<td border="0" colspan="3">'
        # Print candidates
        if not node.is_leaf and len(node.candidates):
            label += 'Candidates:<B> '
            for cand in node.candidates:
                label += cand
            label += '</B>'
        # Print a space in order to preserve row height
        elif node.is_leaf:
            label += '&uarr;'
        label += '</td>'
        if len(node.vp) or len(node.ve) or len(node.vE) or len(node.ip) or len(node.ie) or len(node.eq):
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
            label += '</td>'
        label += '</tr>'
        if not node.is_leaf and node.assignee != '':
            label += '<tr><td border="0" colspan="3">Assignee:<B> ' + node.assignee + '</B></td>'
        elif node.is_leaf:
            label += '<tr><td border="0" colspan="2">' + node.relation.name + '('
            for attr in node.relation.primary_key:
                if attr in node.relation.plain_attr:
                    label += attr
                else:
                    label += '<font color="firebrick">' + attr + '</font>'
            for attr in node.relation.plain_attr:
                if attr not in node.relation.primary_key:
                    label += attr
            label += '<font color="firebrick">'
            for attr in node.relation.enc_attr:
                if attr not in node.relation.primary_key:
                    label += attr
            label += '</font>)</td></tr>'
        if len(node.vp) or len(node.ve) or len(node.vE) or len(node.ip) or len(node.ie) or len(node.eq):
            # eq sets need to be printed with ; in order to separate them
            if label.endswith('</tr>'):
                label = label[:-5]
            label += '<td>'
            for collection in node.eq:
                for attr in collection:
                    label += attr
                label += ';'
            label += '</td></tr>'
        if node.is_leaf:
            label += '<tr><td border="0" colspan="3">@' + node.relation.storage_provider.upper() + '</td></tr>'
        label += '</table>>'
        label += 'shape=plain'
        if not node.eq:
            label += ' '
    return label
