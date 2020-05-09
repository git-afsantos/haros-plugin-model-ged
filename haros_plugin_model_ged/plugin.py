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
        import:
            - config_name
        truth:
            nodes:
                /full/name:
                    node_type: pkg/type
                    args: []
                    conditions:
                        - - statement: if
                            condition: x == 0
                            package: pkg
                            file: path/to/file
                            line: 1
                            column: 1
                    traceability:
                        package: pkg
                        file: path/to/file.launch
                        line: 42
                        column: 1
                    publishers:
                        - topic: /rosname
                          rosname: /before_remaps
                          msg_type: std_msgs/Empty
                          queue_size: 10
                          conditions: []
                          traceability:
                            package: pkg
                            file: src/file.cpp
                            line: 29
                            column: 1
                    subscribers: []
                    servers: []
                    clients: []
                    setters: []
                    getters: []
            parameters:
                /full/name:
                    default_value: null
                    default_type: str
                    conditions: []
                    traceability:
                        package: pkg
                        file: path/to/file.launch
                        line: 42
                        column: 1
"""


###############################################################################
# Imports
###############################################################################

from builtins import range

from timeit import default_timer as timer

from .ged import calc_edit_paths, diff_from_paths, sizeof_graph
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
    # ---- SETUP PHASE ---------------------------------------------------------
    start_time = timer()
    base = new_base()
    build_base(base, attr.get("imports", ()), iface)
    update_base(base, truth)
    Gt = truth_to_nx(base)
    Gp = config_to_nx(config)
    end_time = timer()
    setup_time = end_time - start_time
    # ---- GED0 PHASE ----------------------------------------------------------
    start_time = timer()
    paths, s_ged = calc_edit_paths(Gt, Gp, lvl=0)
    end_time = timer()
    ged0_time = end_time - start_time
    # ---- GED1 PHASE ----------------------------------------------------------
    start_time = timer()
    paths, m_ged = calc_edit_paths(Gt, Gp, lvl=1)
    end_time = timer()
    ged1_time = end_time - start_time
    # ---- GED2 PHASE ----------------------------------------------------------
    start_time = timer()
    paths, f_ged = calc_edit_paths(Gt, Gp, lvl=2)
    end_time = timer()
    ged2_time = end_time - start_time
    # ---- REPORTING PHASE -----------------------------------------------------
    iface.report_metric("simpleGED", s_ged)
    iface.report_metric("midGED", m_ged)
    iface.report_metric("fullGED", f_ged)
    diff = diff_from_paths(paths, Gt, Gp)
    details = issue(s_ged, m_ged, f_ged, Gt, diff)
    iface.report_runtime_violation("reportGED", details)
    write_txt("ged-output.txt", Gt, Gp, paths, diff,
        setup_time=setup_time, ged0_time=ged0_time,
        ged1_time=ged1_time, ged2_time=ged2_time)
    iface.export_file("ged-output.txt")


###############################################################################
# Helper Functions
###############################################################################

def new_base():
    return {"nodes": {}, "parameters": {}}


def build_base(base, config_names, iface):
    for config_name in config_names:
        config = iface.find_configuration(config_name)
        attr = config.user_attributes["haros_plugin_model_ged"]
        build_base(base, attr.get("imports", ()), iface)
        update_base(base, attr["truth"])

def update_base(base, truth):
    base["nodes"].update(truth.get("nodes", {}))
    base["parameters"].update(truth.get("parameters", {}))


def issue(s_ged, m_ged, f_ged, G, diff):
    n_nodes = len(G.nodes)
    n_edges = len(G.edges)
    n = n_nodes + n_edges
    t = sizeof_graph(G)
    err_s = s_ged / t
    err_m = m_ged / t
    err_f = f_ged / t
    return (
        "<p>Graph Item Count: {}</p>\n"
        "<p>Graph Node Count: {}</p>\n"
        "<p>Graph Edge Count: {}</p>\n"
        "<p>Atomic Attribute Count: {}</p>\n"
        "<p>Minimal Graph Edit Distance: {} ({} error rate)</p>\n"
        "<p>Basic Graph Edit Distance: {} ({} error rate)</p>\n"
        "<p>Extended Graph Edit Distance: {} ({} error rate)</p>\n"
        "{}"
    ).format(n, n_nodes, n_edges, t,
        s_ged, err_s, m_ged, err_m, f_ged, err_f, diff_to_html(diff))
