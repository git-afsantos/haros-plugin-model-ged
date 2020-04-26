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
# Notes
###############################################################################

# YAML Ground Truth Format
"""
user_data:
    haros_plugin_model_ged:
        truth:
            launch:
                nodes:
                    - rosname: /full/name
                      node_type: pkg/type
                      args: []
                      conditional: false
                      traceability:
                        package: pkg
                        file: path/to/file.launch
                        line: 42
                parameters:
                    - rosname: /full/name
                      default_value: null
                      conditional: false
                      traceability:
                        package: pkg
                        file: path/to/file.launch
                        line: 42
            links:
                publishers:
                    - node: /rosname
                      topic: /rosname
                      rosname: /before_remaps
                      msg_type: std_msgs/Empty
                      queue_size: 10
                      conditional: false
                      traceability:
                        package: pkg
                        file: src/file.cpp
                        line: 29
                subscribers: []
                servers: []
                clients: []
                sets: []
                gets: []
"""


###############################################################################
# Imports
###############################################################################

from .ged import calc_edit_paths, diff_from_paths
from .haros2nx import config_to_nx, truth_to_nx
from .output_format import diff_to_html, write_txt

###############################################################################
# Plugin Entry Point
###############################################################################

def configuration_analysis(iface, config):
    attr = config.user_attributes.get("haros_plugin_model_ged")
    if attr is None:
        return
    truth = attr.get("truth")
    if truth is None:
        return
    truth = truth_to_nx(truth)
    n = len(truth.nodes) + len(truth.edges)
    model = config_to_nx(config)
    paths, s_ged = calc_edit_paths(truth, model)
    model = config_to_nx(config, ext=True)
    paths, f_ged = calc_edit_paths(truth, model)
    iface.report_metric("simpleGED", s_ged)
    iface.report_metric("fullGED", f_ged)
    diff = diff_from_paths(paths, truth, model)
    iface.report_runtime_violation("reportGED", issue(s_ged, f_ged, n, diff))
    write_txt("ged-output.txt", truth, model, paths, diff)
    iface.export_file("ged-output.txt")


def issue(s_ged, f_ged, n, diff):
    return (
        "<p>Graph Item Count: {}</p>\n"
        "<p>Simple Graph Edit Distance: {} ({} error rate)</p>\n"
        "<p>Full Attr. Graph Edit Distance: {} ({} error rate)</p>\n"
        "{}"
    ).format(n, s_ged, s_ged / n, f_ged, f_ged / n, diff_to_html(diff))
