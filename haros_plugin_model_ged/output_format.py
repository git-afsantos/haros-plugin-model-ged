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


def perf_report_html(r, setup_time):
    parts = []
    parts.append("<p>Setup time: {} seconds</p>".format(setup_time))
    parts.append("<p>Matching time: {} seconds</p>".format(r.match_time))
    parts.append("<p>Report time: {} seconds</p>".format(r.report_time))
    parts.append(HTML_TABLE_TOP)
    parts.append(HTML_TABLE_ROW1.format("Overall", r.overall))
    parts.append(HTML_TABLE_ROW2.format("Launch", r.by.launch))
    parts.append(HTML_TABLE_ROW1.format("Source", r.by.source))
    parts.append(HTML_TABLE_ROW2.format("Node", r.by.node))
    parts.append(HTML_TABLE_ROW1.format("Parameter", r.by.parameter))
    parts.append(HTML_TABLE_ROW2.format("Publisher", r.by.publisher))
    parts.append(HTML_TABLE_ROW1.format("Subscriber", r.by.subscriber))
    parts.append(HTML_TABLE_ROW2.format("Client", r.by.client))
    parts.append(HTML_TABLE_ROW1.format("Server", r.by.server))
    parts.append(HTML_TABLE_ROW2.format("Setter", r.by.setter))
    parts.append(HTML_TABLE_ROW1.format("Getter", r.by.getter))
    parts.append("</tbody>\n</table>")
    return "\n".join(parts)



HTML_TABLE_TOP = \
"""<style type="text/css">
.tg  {border-collapse:collapse;border-color:#ccc;border-spacing:0;border-style:solid;border-width:1px;}
.tg td{background-color:#fff;border-color:#ccc;border-style:solid;border-width:0px;color:#333;
  font-family:Arial, sans-serif;font-size:14px;overflow:hidden;padding:10px 5px;word-break:normal;}
.tg th{background-color:#f0f0f0;border-color:#ccc;border-style:solid;border-width:0px;color:#333;
  font-family:Arial, sans-serif;font-size:14px;font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}
.tg .tg-baqh{text-align:center;vertical-align:top}
.tg .tg-buh4{background-color:#f9f9f9;text-align:left;vertical-align:top}
.tg .tg-h2gs{background-color:#f9f9f9;font-style:italic;text-align:right;vertical-align:top}
.tg .tg-lqy6{text-align:right;vertical-align:top}
.tg .tg-amwm{font-weight:bold;text-align:center;vertical-align:top}
.tg .tg-ps8l{background-color:#f9f9f9;font-style:italic;text-align:center;vertical-align:top}
.tg .tg-ufyb{font-style:italic;text-align:right;vertical-align:top}
.tg .tg-0lax{text-align:left;vertical-align:top}
</style>
<table class="tg">
<thead>
  <tr>
    <th class="tg-baqh"></th>
    <th class="tg-amwm" colspan="3">Level 1</th>
    <th class="tg-amwm" colspan="3">Level 2</th>
    <th class="tg-amwm" colspan="3">Level 3</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td class="tg-buh4"></td>
    <td class="tg-ps8l">Precision</td>
    <td class="tg-ps8l">Recall</td>
    <td class="tg-ps8l">F1-score</td>
    <td class="tg-ps8l">Precision</td>
    <td class="tg-ps8l">Recall</td>
    <td class="tg-ps8l">F1-score</td>
    <td class="tg-ps8l">Precision</td>
    <td class="tg-ps8l">Recall</td>
    <td class="tg-ps8l">F1-score</td>
  </tr>"""

HTML_TABLE_ROW1 = \
"""  <tr>
    <td class="tg-ufyb">{0}</td>
    <td class="tg-0lax">{1.lv1.pre}</td>
    <td class="tg-0lax">{1.lv1.rec}</td>
    <td class="tg-0lax">{1.lv1.f1}</td>
    <td class="tg-0lax">{1.lv2.pre}<br></td>
    <td class="tg-0lax">{1.lv2.rec}</td>
    <td class="tg-0lax">{1.lv2.f1}</td>
    <td class="tg-0lax">{1.lv3.pre}</td>
    <td class="tg-0lax">{1.lv3.rec}</td>
    <td class="tg-0lax">{1.lv3.f1}</td>
  </tr>"""

HTML_TABLE_ROW2 = \
"""  <tr>
    <td class="tg-h2gs">{0}</td>
    <td class="tg-buh4">{1.lv1.pre}</td>
    <td class="tg-buh4">{1.lv1.rec}</td>
    <td class="tg-buh4">{1.lv1.f1}</td>
    <td class="tg-buh4">{1.lv2.pre}<br></td>
    <td class="tg-buh4">{1.lv2.rec}</td>
    <td class="tg-buh4">{1.lv2.f1}</td>
    <td class="tg-buh4">{1.lv3.pre}</td>
    <td class="tg-buh4">{1.lv3.rec}</td>
    <td class="tg-buh4">{1.lv3.f1}</td>
  </tr>"""


###############################################################################
# Text Formatting
###############################################################################

def write_txt(fname, truth, model, paths, diff, setup_time=None, ged0_time=None,
              ged1_time=None, ged2_time=None):
    with open(fname, "w") as f:
        f.write("{}\n".format("\n".join([
            "---- TIMES ----",
            "setup time: {}".format(setup_time),
            "GED0 time: {}".format(ged0_time),
            "GED1 time: {}".format(ged1_time),
            "GED2 time: {}".format(ged2_time),
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




LATEX_TABLE_TOP = """
\begin{table}[]
\begin{tabular}{rlllllllll}
\multicolumn{1}{c}{} & \multicolumn{3}{c}{\textbf{Level 1}}
& \multicolumn{3}{c}{\textbf{Level 2}}
& \multicolumn{3}{c}{\textbf{Level 3}} \\
\multicolumn{1}{l}{} & \multicolumn{1}{c}{\textit{Precision}}
& \multicolumn{1}{c}{\textit{Recall}}
& \multicolumn{1}{c}{\textit{F1-score}}
& \multicolumn{1}{c}{\textit{Precision}}
& \multicolumn{1}{c}{\textit{Recall}}
& \multicolumn{1}{c}{\textit{F1-score}}
& \multicolumn{1}{c}{\textit{Precision}}
& \multicolumn{1}{c}{\textit{Recall}}
& \multicolumn{1}{c}{\textit{F1-score}} \\
"""

LATEX_TABLE_BOT = """
\end{tabular}
\end{table}
"""

LATEX_TABLE_ROW = """
\textit{{{0}}} & {1.lv1.pre} & {1.lv1.rec} & {1.lv1.f1}
& {1.lv2.pre} & {1.lv2.rec} & {1.lv2.f1}
& {1.lv3.pre} & {1.lv3.rec} & {1.lv3.f1} \\
"""
