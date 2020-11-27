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

from builtins import str
from builtins import range
from cgi import escape

###############################################################################
# HTML Formatting
###############################################################################

def perf_report_html(report, setup_time, hc_nodes):
    parts = []
    parts.append("<p>Setup time: {} seconds</p>".format(setup_time))
    parts.append("<p>Matching time: {} seconds</p>".format(report.match_time))
    parts.append("<p>Report time: {} seconds</p>".format(report.report_time))
    nr = report.resource.node.metrics["rosname"]
    n = nr.cor + nr.inc + nr.par + nr.mis
    parts.append("<p>Hard-coded nodes: <b>{}</b> out of <b>{}</b></p>".format(
        hc_nodes, n))
    parts.append(CSS_STYLE)
    _html_table(report, parts, "All Attributes", "*")
    _html_table(report, parts, "ROS Name", "rosname")
    _html_table(report, parts, "ROS Type", "rostype")
    _html_table(report, parts, "Traceability", "traceability")
    _html_table(report, parts, "Conditions", "conditions")
    _perf_report_html_diffs(report, parts)
    return "\n".join(parts)

def _html_table(report, parts, header, attr):
    parts.append(HTML_TABLE_TOP.format(attr=header))
    _html_table_row("Overall", report.aggregate.overall[attr], False, parts)
    _html_table_row("Launch", report.aggregate.launch[attr], True, parts)
    _html_table_row("Source", report.aggregate.source[attr], False, parts)
    _html_table_row("Topic Links", report.aggregate.topics[attr], True, parts)
    _html_table_row("Service Links", report.aggregate.services[attr], False, parts)
    _html_table_row("Param. Links", report.aggregate.params[attr], True, parts)
    _html_table_row("Node", report.resource.node.metrics[attr], False, parts)
    _html_table_row("Parameter", report.resource.parameter.metrics[attr], True, parts)
    _html_table_row("Publisher", report.resource.publisher.metrics[attr], False, parts)
    _html_table_row("Subscriber", report.resource.subscriber.metrics[attr], True, parts)
    _html_table_row("Client", report.resource.client.metrics[attr], False, parts)
    _html_table_row("Server", report.resource.server.metrics[attr], True, parts)
    _html_table_row("Setter", report.resource.setter.metrics[attr], False, parts)
    _html_table_row("Getter", report.resource.getter.metrics[attr], True, parts)
    parts.append("</tbody>\n</table>")

def _html_table_row(name, r, shadow, parts):
    temp = HTML_TABLE_ROW2 if shadow else HTML_TABLE_ROW1
    values = [
        ("", r.cor), ("", r.inc), ("", r.par), ("", r.mis), ("", r.spu),
        _html_colorize(r.pre), _html_colorize(r.rec), _html_colorize(r.f1)
    ]
    parts.append(temp.format(name, values))

def _html_colorize(value):
    if value <= 0.5:
        return ("-red", "{:.4f}".format(value))
    if value <= 0.8:
        return ("-yellow", "{:.4f}".format(value))
    if value < 1.0:
        return ("-green", "{:.4f}".format(value))
    return ("", "{:.4f}".format(value))


CSS_STYLE = \
"""<style type="text/css">
.tg  {border-collapse:collapse;border-color:#ccc;border-spacing:0;border-style:solid;border-width:1px;}
.tg td{background-color:#fff;border-color:#ccc;border-style:solid;border-width:0px;color:#333;
  font-family:Arial, sans-serif;font-size:14px;overflow:hidden;padding:10px 5px;word-break:normal;}
.tg th{background-color:#f0f0f0;border-color:#ccc;border-style:solid;border-width:0px;color:#333;
  font-family:Arial, sans-serif;font-size:14px;font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}
.tg .tg-baqh{text-align:center;vertical-align:top}
.tg .tg-buh4{background-color:#f9f9f9;text-align:center;vertical-align:top}
.tg .tg-buh4-red{background-color:#f9f9f9;text-align:center;vertical-align:top;color:#cb4335}
.tg .tg-buh4-yellow{background-color:#f9f9f9;text-align:center;vertical-align:top;color:#f39c12}
.tg .tg-buh4-green{background-color:#f9f9f9;text-align:center;vertical-align:top;color:#229954}
.tg .tg-h2gs{background-color:#f9f9f9;font-style:italic;text-align:right;vertical-align:top}
.tg .tg-lqy6{text-align:right;vertical-align:top}
.tg .tg-amwm{font-weight:bold;text-align:center;vertical-align:top}
.tg .tg-ps8l{background-color:#f9f9f9;font-style:italic;text-align:center;vertical-align:top}
.tg .tg-ufyb{font-style:italic;text-align:right;vertical-align:top}
.tg .tg-0lax{text-align:center;vertical-align:top}
.tg .tg-0lax-red{text-align:center;vertical-align:top;color:#cb4335}
.tg .tg-0lax-yellow{text-align:center;vertical-align:top;color:#f39c12}
.tg .tg-0lax-green{text-align:center;vertical-align:top;color:#229954}
.rosname {font-family: monospace;unicode-bidi: embed;font-weight:bold;color:#229954}
</style>
"""

HTML_TABLE_TOP = \
"""
<table class="tg">
<thead>
  <tr>
    <th class="tg-amwm" colspan="9">{attr}</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td class="tg-buh4"></td>
    <td class="tg-ps8l">COR</td>
    <td class="tg-ps8l">INC</td>
    <td class="tg-ps8l">PAR</td>
    <td class="tg-ps8l">MIS</td>
    <td class="tg-ps8l">SPU</td>
    <td class="tg-ps8l">Precision</td>
    <td class="tg-ps8l">Recall</td>
    <td class="tg-ps8l">F1-score</td>
  </tr>"""

HTML_TABLE_ROW1 = \
"""  <tr>
    <td class="tg-ufyb">{0}</td>
    <td class="tg-0lax{1[0][0]}">{1[0][1]}</td>
    <td class="tg-0lax{1[1][0]}">{1[1][1]}</td>
    <td class="tg-0lax{1[2][0]}">{1[2][1]}</td>
    <td class="tg-0lax{1[3][0]}">{1[3][1]}</td>
    <td class="tg-0lax{1[4][0]}">{1[4][1]}</td>
    <td class="tg-0lax{1[5][0]}">{1[5][1]}</td>
    <td class="tg-0lax{1[6][0]}">{1[6][1]}</td>
    <td class="tg-0lax{1[7][0]}">{1[7][1]}</td>
  </tr>"""

HTML_TABLE_ROW2 = \
"""  <tr>
    <td class="tg-h2gs">{0}</td>
    <td class="tg-buh4{1[0][0]}">{1[0][1]}</td>
    <td class="tg-buh4{1[1][0]}">{1[1][1]}</td>
    <td class="tg-buh4{1[2][0]}">{1[2][1]}</td>
    <td class="tg-buh4{1[3][0]}">{1[3][1]}</td>
    <td class="tg-buh4{1[4][0]}">{1[4][1]}</td>
    <td class="tg-buh4{1[5][0]}">{1[5][1]}</td>
    <td class="tg-buh4{1[6][0]}">{1[6][1]}</td>
    <td class="tg-buh4{1[7][0]}">{1[7][1]}</td>
  </tr>"""


def _perf_report_html_diffs(report, parts):
    parts.append("<p>Attribute diffs:")
    parts.append("<ul>")
    for attr in ("node", "parameter", "publisher", "subscriber",
                 "client", "server", "setter", "getter"):
        diffs = getattr(report.resource, attr).diffs
        for diff in diffs:
            p = diff.p_value
            g = diff.g_value
            if diff.attribute == "*":
                if p is None:
                    li = ('<li>Missing {} <span class="rosname">{}</span> '
                          '<br>{}</li>')
                    s = '<span class="code">{}: {}</span>'
                    spans = [s.format(g._fields[i], escape(str(g[i])))
                             for i in range(1, len(g))]
                    parts.append(li.format(diff.resource_type, diff.rosname,
                        "<br>".join(spans)))
                elif g is None:
                    li = ('<li>Spurious {} <span class="rosname">{}</span> '
                          '<br>{}</li>')
                    s = '<span class="code">{}: {}</span>'
                    spans = [s.format(p._fields[i], escape(str(p[i])))
                             for i in range(1, len(p))]
                    parts.append(li.format(diff.resource_type, diff.rosname,
                        "<br>".join(spans)))
            else:
                li = ('<li>{} <span class="rosname">{}</span> '
                      '[<i>{}:</i> <span class="code">{}</span>'
                      ' should be <span class="code">{}</span>]</li>')
                parts.append(li.format(diff.resource_type, diff.rosname,
                    diff.attribute, escape(str(p)), escape(str(g))))
    parts.append("</ul></p>")


###############################################################################
# Text Formatting
###############################################################################

def write_txt(fname, truth, report):
    parts = []
    parts.append("-------- PARAMS --------")
    for rosname, data in truth.get("parameters", {}).items():
        parts.append("{!r} {}".format(rosname, data))
    parts.append("-------- NODES --------")
    for rosname, data in truth.get("nodes", {}).items():
        parts.append("{!r} {}".format(rosname, data))
    parts.append("-------- REPORT --------")
    parts.append(str(report))
    with open(fname, "w") as f:
        f.write("\n".join(parts))

def write_latex(fname, report):
    parts = []
    parts.append("\definecolor{redvalue}{rgb}{0.8,0.25,0.2}\n")
    parts.append("\definecolor{yellowvalue}{rgb}{0.95,0.6,0}\n")
    parts.append("\definecolor{greenvalue}{rgb}{0.13,0.6,0.33}\n")
    _latex_table(report, parts, "All Attributes", "*")
    _latex_table(report, parts, "ROS Name", "rosname")
    _latex_table(report, parts, "ROS Type", "rostype")
    _latex_table(report, parts, "Traceability", "traceability")
    _latex_table(report, parts, "Conditions", "conditions")
    with open(fname, "w") as f:
        f.write("".join(parts))


def _latex_table(report, parts, header, attr):
    parts.append(LATEX_TABLE_TOP.format(attr=header))
    _latex_row("Overall", report.aggregate.overall[attr], parts)
    _latex_row("Launch", report.aggregate.launch[attr], parts)
    _latex_row("Source", report.aggregate.source[attr], parts)
    _latex_row("Topic Links", report.aggregate.topics[attr], parts)
    _latex_row("Service Links", report.aggregate.services[attr], parts)
    _latex_row("Param. Links", report.aggregate.params[attr], parts)
    _latex_row("Node", report.resource.node.metrics[attr], parts)
    _latex_row("Parameter", report.resource.parameter.metrics[attr], parts)
    _latex_row("Publisher", report.resource.publisher.metrics[attr], parts)
    _latex_row("Subscriber", report.resource.subscriber.metrics[attr], parts)
    _latex_row("Client", report.resource.client.metrics[attr], parts)
    _latex_row("Server", report.resource.server.metrics[attr], parts)
    _latex_row("Setter", report.resource.setter.metrics[attr], parts)
    _latex_row("Getter", report.resource.getter.metrics[attr], parts)
    parts.append(LATEX_TABLE_BOT)

def _latex_row(name, r, parts):
    values = [r.cor, r.inc, r.par, r.mis, r.spu,
        _latex_colorize(r.pre), _latex_colorize(r.rec), _latex_colorize(r.f1)]
    parts.append(LATEX_TABLE_ROW.format(name, values))

def _latex_colorize(value):
    if value <= 0.5:
        return r"{{\color{{redvalue}} {:.3f}}}".format(value)
    if value <= 0.8:
        return r"{{\color{{yellowvalue}} {:.3f}}}".format(value)
    if value < 1.0:
        return r"{{\color{{greenvalue}} {:.3f}}}".format(value)
    return "{:.3f}".format(value)


LATEX_TABLE_TOP = r"""
\begin{{table}}[]
\begin{{tabular}}{{rcccccccc}}
\multicolumn{{9}}{{c}}{{\textbf{{ {attr} }}}} \\
 & \textit{{COR}} & \textit{{INC}} & \textit{{PAR}}
& \textit{{MIS}} & \textit{{SPU}} & \textit{{Precision}}
& \textit{{Recall}} & \textit{{F1-score}} \\
"""

LATEX_TABLE_BOT = r"""
\end{tabular}
\end{table}
"""

LATEX_TABLE_ROW = r"""
\textit{{{0}}} & ${1[0]}$ & ${1[1]}$ & ${1[2]}$ & ${1[3]}$ & ${1[4]}$
& ${1[5]}$ & ${1[6]}$ & ${1[7]}$ \\
"""
