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

def perf_report_html(report, setup_time):
    parts = []
    parts.append("<p>Setup time: {} seconds</p>".format(setup_time))
    parts.append("<p>Matching time: {} seconds</p>".format(report.match_time))
    parts.append("<p>Report time: {} seconds</p>".format(report.report_time))
    _perf_report_html_metrics(report, parts)
    _perf_report_html_table(report, parts)
    _perf_report_html_diffs(report, parts)
    return "\n".join(parts)


def _perf_report_html_metrics(report, parts):
    p = "<p>[Lv.1] Number of {}s: {} ({} COR, {} INC, {} PAR, {} MIS, {} SPU)</p>"
    for attr in ("node", "parameter", "publisher", "subscriber",
                 "client", "server", "setter", "getter"):
        r = getattr(report.by, attr).lv1
        n = r.cor + r.inc + r.par + r.mis
        parts.append(p.format(attr, n, r.cor, r.inc, r.par, r.mis, r.spu))

def _perf_report_html_table(report, parts):
    parts.append(HTML_TABLE_TOP)
    _html_table_row("Overall", report.overall, False, parts)
    _html_table_row("Launch", report.by.launch, True, parts)
    _html_table_row("Source", report.by.source, False, parts)
    _html_table_row("Node", report.by.node, True, parts)
    _html_table_row("Parameter", report.by.parameter, False, parts)
    _html_table_row("Publisher", report.by.publisher, True, parts)
    _html_table_row("Subscriber", report.by.subscriber, False, parts)
    _html_table_row("Client", report.by.client, True, parts)
    _html_table_row("Server", report.by.server, False, parts)
    _html_table_row("Setter", report.by.setter, True, parts)
    _html_table_row("Getter", report.by.getter, False, parts)
    parts.append("</tbody>\n</table>")

def _html_table_row(name, r, shadow, parts):
    temp = HTML_TABLE_ROW2 if shadow else HTML_TABLE_ROW1
    values = [
        r.lv1.pre, r.lv1.rec, r.lv1.f1,
        r.lv2.pre, r.lv2.rec, r.lv2.f1,
        r.lv3.pre, r.lv3.rec, r.lv3.f1
    ]
    values = map(_html_colorize, values)
    parts.append(temp.format(name, values))

def _html_colorize(value):
    if value <= 0.5:
        return ("-red", "{:.4f}".format(value))
    if value <= 0.8:
        return ("-yellow", "{:.4f}".format(value))
    if value < 1.0:
        return ("-green", "{:.4f}".format(value))
    return ("", "{:.4f}".format(value))


HTML_TABLE_TOP = \
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
    <td class="tg-0lax{1[0][0]}">{1[0][1]}</td>
    <td class="tg-0lax{1[1][0]}">{1[1][1]}</td>
    <td class="tg-0lax{1[2][0]}">{1[2][1]}</td>
    <td class="tg-0lax{1[3][0]}">{1[3][1]}</td>
    <td class="tg-0lax{1[4][0]}">{1[4][1]}</td>
    <td class="tg-0lax{1[5][0]}">{1[5][1]}</td>
    <td class="tg-0lax{1[6][0]}">{1[6][1]}</td>
    <td class="tg-0lax{1[7][0]}">{1[7][1]}</td>
    <td class="tg-0lax{1[8][0]}">{1[8][1]}</td>
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
    <td class="tg-buh4{1[8][0]}">{1[8][1]}</td>
  </tr>"""


def _perf_report_html_diffs(report, parts):
    parts.append("<p>Attribute diffs:")
    parts.append("<ul>")
    for attr in ("node", "parameter", "publisher", "subscriber",
                 "client", "server", "setter", "getter"):
        diffs = getattr(report.by, attr).diffs
        for diff in diffs:
            p = diff.p_value
            g = diff.g_value
            if diff.attribute == "*":
                if p is None:
                    li = '<li>Missing {} "{}" <span class="code">{}</span></li>'
                    parts.append(li.format(diff.resource_type, diff.rosname,
                        escape(str(g))))
                elif g is None:
                    li = '<li>Spurious {} "{}" <span class="code">{}</span></li>'
                    parts.append(li.format(diff.resource_type, diff.rosname,
                        escape(str(p))))
            else:
                li = ('<li>{} "{}" [<i>{}:</i> <span class="code">{}</span>'
                      ' should be <span class="code">{}</span>]</li>')
                parts.append(li.format(diff.resource_type, diff.rosname,
                    diff.attribute, escape(str(p)), escape(str(g))))
    parts.append("</ul></p>")


###############################################################################
# Text Formatting
###############################################################################

def write_latex(fname, report):
    parts = [LATEX_TABLE_TOP]
    parts.append(LATEX_TABLE_ROW.format("Overall", report.overall))
    parts.append(LATEX_TABLE_ROW.format("Launch", report.by.launch))
    parts.append(LATEX_TABLE_ROW.format("Source", report.by.source))
    parts.append(LATEX_TABLE_ROW.format("Node", report.by.node))
    parts.append(LATEX_TABLE_ROW.format("Parameter", report.by.parameter))
    parts.append(LATEX_TABLE_ROW.format("Publisher", report.by.publisher))
    parts.append(LATEX_TABLE_ROW.format("Subscriber", report.by.subscriber))
    parts.append(LATEX_TABLE_ROW.format("Client", report.by.client))
    parts.append(LATEX_TABLE_ROW.format("Server", report.by.server))
    parts.append(LATEX_TABLE_ROW.format("Setter", report.by.setter))
    parts.append(LATEX_TABLE_ROW.format("Getter", report.by.getter))
    parts.append(LATEX_TABLE_BOT)
    with open(fname, "w") as f:
        f.write("".join(parts))


LATEX_TABLE_TOP = r"""
\begin{table}[]
\begin{tabular}{rccccccccc}
 & \multicolumn{3}{c}{\textbf{Level 1}}
& \multicolumn{3}{c}{\textbf{Level 2}}
& \multicolumn{3}{c}{\textbf{Level 3}} \\
 & \textit{Precision}
& \textit{Recall}
& \textit{F1-score}
& \textit{Precision}
& \textit{Recall}
& \textit{F1-score}
& \textit{Precision}
& \textit{Recall}
& \textit{F1-score} \\
"""

LATEX_TABLE_BOT = r"""
\end{tabular}
\end{table}
"""

LATEX_TABLE_ROW = r"""
\textit{{{0}}} & {1.lv1.pre:.3f} & {1.lv1.rec:.3f} & {1.lv1.f1:.3f}
& {1.lv2.pre:.3f} & {1.lv2.rec:.3f} & {1.lv2.f1:.3f}
& {1.lv3.pre:.3f} & {1.lv3.rec:.3f} & {1.lv3.f1:.3f} \\
"""
