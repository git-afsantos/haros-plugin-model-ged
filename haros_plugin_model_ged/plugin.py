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

from .graph_diff import calc_performance
from .output_format import perf_report_html, write_latex, write_txt

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
    # ---- SETUP PHASE --------------------------------------------------------
    start_time = timer()
    base = new_base()
    build_base(base, attr.get("import", ()), iface)
    update_base(base, truth)
    end_time = timer()
    setup_time = end_time - start_time
    # ---- REPORT PHASE -------------------------------------------------------
    report = calc_performance(config, base)
    iface.report_metric("precision", report.overall.lv3.pre)
    iface.report_metric("recall", report.overall.lv3.rec)
    iface.report_metric("f1", report.overall.lv3.f1)
    iface.report_runtime_violation("reportPerformance",
        perf_report_html(report, setup_time))
    fname = "perf-metrics-{}.tex".format(config.name)
    write_latex(fname, report)
    iface.export_file(fname)
    fname = "dump-{}.txt".format(config.name)
    write_txt(fname, base)
    iface.export_file(fname)


###############################################################################
# Helper Functions
###############################################################################

def new_base():
    return {"nodes": {}, "parameters": {}}


def build_base(base, config_names, iface):
    for config_name in config_names:
        config = iface.find_configuration(config_name)
        attr = config.user_attributes["haros_plugin_model_ged"]
        build_base(base, attr.get("import", ()), iface)
        update_base(base, attr["truth"])

def update_base(base, truth):
    base["nodes"].update(truth.get("nodes", {}))
    base["parameters"].update(truth.get("parameters", {}))
