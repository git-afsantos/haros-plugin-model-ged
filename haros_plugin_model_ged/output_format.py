# -*- coding: utf-8 -*-

#Copyright (c) 2020 André Santos
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.


###############################################################################
# Imports
###############################################################################

from cgi import escape

###############################################################################
# HTML Formatting
###############################################################################

def diff_to_html(diff):
    parts = []
    if diff.missed_nodes or diff.missed_edges:
        parts.append("<p>Missing:")
        parts.append("<ul>")
        for ntype, nid in diff.missed_nodes:
            name = nid.split("]")[-1]
            parts.append('<li>{} "{}"</li>'.format(ntype, name))
        for etype, nid1, nid2 in diff.missed_edges:
            name1 = nid1.split("]")[-1]
            name2 = nid2.split("]")[-1]
            parts.append('<li>{} "{}" &#8594; "{}"</li>'.format(
                etype, name1, name2))
        parts.append("</ul></p>")
    if diff.spurious_nodes or diff.spurious_edges:
        parts.append("<p>Spurious:")
        parts.append("<ul>")
        for ntype, nid in diff.spurious_nodes:
            name = nid.split("]")[-1]
            parts.append('<li>{} "{}"</li>'.format(ntype, name))
        for etype, nid1, nid2 in diff.spurious_edges:
            name1 = nid1.split("]")[-1]
            name2 = nid2.split("]")[-1]
            parts.append('<li>{} "{}" &#8594; "{}"</li>'.format(
                etype, name1, name2))
        parts.append("</ul></p>")
    if diff.partial_nodes or diff.partial_edges:
        parts.append("<p>Partial Match:")
        parts.append("<ul>")
        for ntype, nid1, nid2, deltas in diff.partial_nodes:
            name = nid1.split("]")[-1]
            parts.append('<li>{} "{}" [{}]</li>'.format(
                ntype, name, delta_html(deltas)))
        for etype, nid1, nid2, nid3, nid4, deltas in diff.partial_edges:
            name1 = nid1.split("]")[-1]
            name2 = nid2.split("]")[-1]
            parts.append('<li>{} "{}" &#8594; "{}" [{}]</li>'.format(
                etype, name1, name2, delta_html(deltas)))
        parts.append("</ul></p>")
    return "\n".join(parts)


def delta_html(deltas):
    parts = []
    for d in deltas:
        parts.append((
            '<i>{}:</i> '
            '<span class="code">{}</span>'
            ' should be '
            '<span class="code">{}</span>').format(
                d[0], escape(str(d[2])), escape(str(d[1]))))
    return "; ".join(parts)


###############################################################################
# Text Formatting
###############################################################################

def write_txt(fname, truth, model, paths, diff):
    with open(fname, "w") as f:
        f.write("{}\n".format("\n".join([
            "---- TRUTH NODES ----",
            str(truth.nodes.values()),
            "---- TRUTH EDGES ----",
            str(truth.edges.values()),
            "---- MODEL NODES ----",
            str(model.nodes.values()),
            "---- MODEL EDGES ----",
            str(model.edges.values()),
            "---- EDIT PATHS ----",
            format_edit_paths(paths),
            "---- GRAPH DIFF ----",
            format_diff(diff)
        ])))


def format_edit_paths(paths):
    if not paths:
        return "nil"
    parts = []
    for node_list, edge_list in paths:
        parts.extend(format_node_list(node_list))
        parts.extend(format_edge_list(edge_list))
    return "\n".join(parts)

def format_node_list(node_list):
    parts = []
    for u, v in node_list:
        if u is None:
            parts.append("insert('{}')".format(v))
        elif v is None:
            parts.append("remove('{}')".format(u))
        else:
            parts.append("subst('{}', '{}')".format(u, v))
    return parts

def format_edge_list(edge_list):
    parts = []
    for a, b in edge_list:
        if a is None:
            parts.append("insert('{} -> {}')".format(b[0], b[1]))
        elif b is None:
            parts.append("remove('{} -> {}')".format(a[0], a[1]))
        else:
            parts.append("subst('{} -> {}', '{} -> {}')".format(
                a[0], a[1], b[0], b[1]))
    return parts

def format_diff(diff):
    parts = []
    for item in diff.missed_nodes:
        parts.append("missing{}".format(item))
    for item in diff.missed_edges:
        parts.append("missing{}".format(item))
    for item in diff.spurious_nodes:
        parts.append("fantasy{}".format(item))
    for item in diff.spurious_edges:
        parts.append("fantasy{}".format(item))
    for item in diff.partial_nodes:
        parts.append("partial{}".format(item))
    for item in diff.partial_edges:
        parts.append("partial{}".format(item))
    return "\n".join(parts)
