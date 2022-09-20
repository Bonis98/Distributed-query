from anytree.exporter import DotExporter

from node import Node


def export_tree(types, filename, root):
    if types == 'nodes':
        DotExporter(root, nodeattrfunc=node_attr, edgeattrfunc=lambda *args: "dir=back").to_picture(filename)
        return
    if types == 'profiles':
        DotExporter(root, nodeattrfunc=node_profile, edgeattrfunc=lambda *args: "dir=back").to_picture(filename)
        return
    raise ValueError("export: types argument must be one of %r" % ['nodes', 'profiles'])


def node_attr(node: Node):
    # If re-encryption draw a square box half greyed out with its assignee
    if node.re_encryption:
        label = "label=<"
        for attr in node.Ae:
            label += attr
        label += "<BR/><BR/>Assignee:&nbsp;<B>" + node.assignee + "</B>"
        label += ">"
        label += "shape=box, style=filled, fillcolor=\"white;0.5:lightgrey\", gradientangle=90"
    # All the other nodes goes in a normal circle, with candidates and assignee in bold
    else:
        label = node.name
        label = label.replace(">", "&gt;").replace("<", "&lt;")
        label = "label=<" + label
        label = label.replace("Selection", "&sigma;<sub>")
        label = label.replace("Group-by", "&gamma;<sub>")
        label = label.replace("Join", "⋈<sub>")
        label = label.replace("Projection", "&pi;<sub>")
        label += "</sub><br/><br/>"
        # If node is not a leaf node, print candidates
        if not node.is_leaf:
            for cand in node.candidates:
                if cand == node.assignee:
                    label += "<B>" + cand + "</B>"
                    continue
                label += cand
            label += ">"
    # Leaf nodes goes in a square box
    if node.is_leaf:
        label += "Assignee:&nbsp;<B>" + node.assignee + "</B>"
        label += ">"
        label += "shape=box"
    return label


def node_profile(node: Node):
    # If node is a re-encryption operation, no profile is specified
    if node.re_encryption:
        label = "label=<"
        for attr in node.Ae:
            label += attr
        label += ">"
        label += "shape=box, style=filled, fillcolor=\"white;0.5:lightgrey\", gradientangle=90"
    else:
        # Need to determine max len of first and second row in order to fill shorter sets with spaces
        first_len = len(node.vp) if len(node.vp) > len(node.ip) else len(node.ip)
        second_len = len(node.ve) if len(node.ve) > len(node.ie) else len(node.ie)
        # If second row is 0, increment to one for visualization
        if not second_len:
            second_len += 1
        # Print HTML table
        label = "label=<<table border=\"0\" cellborder=\"1\"><tr><td>"
        for attr in node.vp:
            label += attr
        for _ in range(0, first_len - len(node.vp)):
            label += " "
        label += "</td><td>"
        for attr in node.ve:
            label += attr
        for _ in range(0, second_len - len(node.ve)):
            label += " "
        label += "</td><td>"
        for attr in node.vE:
            label += attr
        label += "</td></tr><tr><td>"
        for attr in node.ip:
            label += attr
        for _ in range(0, first_len - len(node.ip)):
            label += " "
        label += "</td><td>"
        for attr in node.ie:
            label += attr
        for _ in range(0, second_len - len(node.ie)):
            label += " "
        label += "</td></tr><tr><td colspan=\"2\">"
        # eq sets need to be printed with ; in order to separate them
        for collection in node.eq:
            for attr in collection:
                label += attr
            label += ";"
        label += "</td></tr></table>>"
        # Leaf nodes goes in a square box
        if node.is_leaf:
            label += " shape=box"
    return label
