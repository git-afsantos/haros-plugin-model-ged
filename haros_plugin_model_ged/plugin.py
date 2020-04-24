# -*- coding: utf-8 -*-

#Copyright (c) 2019 André Santos
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

from builtins import range

import networkx as nx

###############################################################################
# Constants
###############################################################################

NODE = 1
TOPIC = 2
SERVICE = 3
PARAMETER = 4

PUBLISH = 1
SUBSCRIBE = 2
SERVER = 3
CLIENT = 4
GET = 5
SET = 6

###############################################################################
# Plugin Entry Point
###############################################################################

def configuration_analysis(iface, config):
    truth = config.user_attributes.get("haros_plugin_model_ged")
    if truth is None:
        return
    truth = truth_to_nx(truth)
    model = config_to_nx(config)
    s_ged = calc_ged(truth, model)
    model = config_to_nx(config ext=True)
    f_ged = calc_ged(truth, model)
    iface.report_metric("simpleGED", s_ged)
    iface.report_metric("fullGED", f_ged)
    iface.report_runtime_violation("reportGED",
        "Simple GED: {}, Full GED: {}".format(s_ged, f_ged))


###############################################################################
# Graph Node Attributes
###############################################################################

def node_attrs(node, ext=False):
    attrs = {
        "resource_type": NODE,
        "rosname": node.rosname.full,
        # "rosname": node.rosname.own,
        # "namespace": node.rosname.namespace
    }
    if ext:
        loc = node.traceability()[0]
        if loc is None:
            loc = {"package": None, "file": None, "line": None}
        else:
            loc = {
                "package": loc.package,
                "file": loc.file,
                "line": loc.line
            }
        attrs.update({
            "node_type": node.node_name,
            "args": node.argv,
            "conditional": bool(node.conditions),
            "traceability": loc
        })
    return attrs

def topic_attrs(topic, ext=False):
    attrs = {
        "resource_type": TOPIC,
        "rosname": topic.rosname.full,
        # "rosname": topic.rosname.own,
        # "namespace": topic.rosname.namespace
    }
    if ext:
        attrs.update({
            "conditional": bool(topic.conditions),
            "traceability": [{
                "package": loc.package,
                "file": loc.file,
                "line": loc.line
            } for loc in topic.traceability()]
        })
    return attrs

def service_attrs(service, ext=False):
    attrs = {
        "resource_type": SERVICE,
        "rosname": service.rosname.full,
        # "rosname": service.rosname.own,
        # "namespace": service.rosname.namespace
    }
    if ext:
        attrs.update({
            "conditional": bool(service.conditions),
            "traceability": [{
                "package": loc.package,
                "file": loc.file,
                "line": loc.line
            } for loc in service.traceability()]
        })
    return attrs

def param_attrs(param, ext=False):
    attrs = {
        "resource_type": PARAMETER,
        "rosname": param.rosname.full,
        # "rosname": param.rosname.own,
        # "namespace": param.rosname.namespace
    }
    if ext:
        attrs.update({
            "default_value": param.value,
            "conditional": bool(param.conditions),
            "traceability": [{
                "package": loc.package,
                "file": loc.file,
                "line": loc.line
            } for loc in param.traceability()]
        })
    return attrs


###############################################################################
# Graph Edge Attributes
###############################################################################

def topiclink_attrs(link, t, ext=False):
    attrs = {
        "link_type": t,
    }
    if ext:
        if link.source_location is None:
            loc = {"package": None, "file": None, "line": None}
        else:
            loc = {
                "package": link.source_location.package,
                "file": link.source_location.file,
                "line": link.source_location.line
            }
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": loc,
            "queue_size": link.queue_size,
            "msg_type": link.type
        })
    return attrs

def srvlink_attrs(link, t, ext=False):
    attrs = {
        "link_type": t,
    }
    if ext:
        if link.source_location is None:
            loc = {"package": None, "file": None, "line": None}
        else:
            loc = {
                "package": link.source_location.package,
                "file": link.source_location.file,
                "line": link.source_location.line
            }
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": loc,
            "srv_type": link.type
        })
    return attrs

def paramlink_attrs(link, t, ext=False):
    attrs = {
        "link_type": t,
    }
    if ext:
        if link.source_location is None:
            loc = {"package": None, "file": None, "line": None}
        else:
            loc = {
                "package": link.source_location.package,
                "file": link.source_location.file,
                "line": link.source_location.line
            }
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": loc,
            "param_type": link.type
        })
    return attrs


###############################################################################
# HAROS to NetworkX Conversion
###############################################################################

def config_to_nx(config, ext=False):
    G = nx.MultiDiGraph()
    for node in config.nodes.enabled:
        attrs = node_attrs(node, ext=ext)
        G.add_node(id(node), attrs)
    for topic in config.topics.enabled:
        attrs = topic_attrs(topic, ext=ext)
        G.add_node(id(topic), attrs)
    for service in config.services.enabled:
        attrs = service_attrs(service, ext=ext)
        G.add_node(id(service), attrs)
    for param in config.parameters.enabled:
        attrs = param_attrs(param, ext=ext)
        G.add_node(id(param), attrs)
    for node in config.nodes.enabled:
        for link in node.publishers:
            attrs = topiclink_attrs(link, PUBLISH, ext=ext)
            s = id(link.node)
            t = id(link.topic)
            G.add_edge(s, t, key=id(link), attrs)
        for link in node.subscribers:
            attrs = topiclink_attrs(link, SUBSCRIBE, ext=ext)
            s = id(link.topic)
            t = id(link.node)
            G.add_edge(s, t, key=id(link), attrs)
        for link in node.servers:
            attrs = srvlink_attrs(link, SERVICE, ext=ext)
            s = id(link.service)
            t = id(link.node)
            G.add_edge(s, t, key=id(link), attrs)
        for link in node.clients:
            attrs = srvlink_attrs(link, CLIENT, ext=ext)
            s = id(link.node)
            t = id(link.service)
            G.add_edge(s, t, key=id(link), attrs)
        for link in node.reads:
            attrs = paramlink_attrs(link, GET, ext=ext)
            s = id(link.parameter)
            t = id(link.node)
            G.add_edge(s, t, key=id(link), attrs)
        for link in node.writes:
            attrs = paramlink_attrs(link, SET, ext=ext)
            s = id(link.node)
            t = id(link.parameter)
            G.add_edge(s, t, key=id(link), attrs)
    return G


###############################################################################
# Ground Truth to NetworkX Conversion
###############################################################################

def truth_to_nx(truth):
    G = nx.MultiDiGraph()
    for node in truth["nodes"]:
        attrs = dict(node)
        uid = attrs["id"]
        del attrs["id"]
        attrs["resource_type"] = NODE
        G.add_node(uid, attrs)
    for topic in truth["topics"]:
        attrs = dict(topic)
        uid = attrs["id"]
        del attrs["id"]
        attrs["resource_type"] = TOPIC
        G.add_node(uid, attrs)
    for service in truth["services"]:
        attrs = dict(service)
        uid = attrs["id"]
        del attrs["id"]
        attrs["resource_type"] = SERVICE
        G.add_node(uid, attrs)
    for param in truth["parameters"]:
        attrs = dict(param)
        uid = attrs["id"]
        del attrs["id"]
        attrs["resource_type"] = PARAMETER
        G.add_node(uid, attrs)
    for link in truth["publish"]:
        s = link["node"]
        t = link["topic"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["topic"]
        attrs["link_type"] = PUBLISH
        G.add_edge(s, t, attrs)
    for link in truth["subscribe"]:
        s = link["topic"]
        t = link["node"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["topic"]
        attrs["link_type"] = SUBSCRIBE
        G.add_edge(s, t, attrs)
    for link in truth["client"]:
        s = link["node"]
        t = link["service"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["service"]
        attrs["link_type"] = CLIENT
        G.add_edge(s, t, attrs)
    for link in truth["server"]:
        s = link["service"]
        t = link["node"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["service"]
        attrs["link_type"] = SERVER
        G.add_edge(s, t, attrs)
    for link in truth["set_param"]:
        s = link["node"]
        t = link["parameter"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["parameter"]
        attrs["link_type"] = SET
        G.add_edge(s, t, attrs)
    for link in truth["get_param"]:
        s = link["parameter"]
        t = link["node"]
        attrs = dict(link)
        del attrs["node"]
        del attrs["parameter"]
        attrs["link_type"] = GET
        G.add_edge(s, t, attrs)
    return G


###############################################################################
# Graph Edit Distance Calculation
###############################################################################

def calc_ged(truth, config):
    G1 = truth_to_nx(truth)
    G2 = config_to_nx(config)
    return nx.graph_edit_distance(G1, G2,
        node_subst_cost=node_subst_cost,
        node_del_cost=None, # defaults to 1
        node_ins_cost=None, # defaults to 1
        edge_subst_cost=edge_subst_cost,
        edge_del_cost=None, # defaults to 1
        edge_ins_cost=None) # defaults to 1


###############################################################################
# GED Node Cost Functions
###############################################################################

# node_subst_cost(G1.nodes[n1], G2.nodes[n2])
# node_del_cost(G1.nodes[n1])
# node_ins_cost(G2.nodes[n2])

def node_subst_cost(u, v):
    # u: graph node from ground truth
    # v: graph node from extracted model
    # should be the dict attributes for each node
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    if u["resource_type"] != v["resource_type"]:
        return 1.0
    n = len(v)
    assert n >= 3
    total = float(n - 1) # ignore 'resource_type'
    score = total # start with everything right and apply penalties
    score -= cmp_resource(u, v)
    if n > 3:
        if u["resource_type"] == NODE:
            score -= cmp_node_ext(u, v)
        elif u["resource_type"] == TOPIC:
            score -= cmp_topic_ext(u, v)
        elif u["resource_type"] == SERVICE:
            score -= cmp_service_ext(u, v)
        else:
            assert u["resource_type"] == PARAMETER
            score -= cmp_param_ext(u, v)
    score = (total - score) / total # normalize
    assert score >= 0.0 and score <= 1.0
    return score


def cmp_resource(u, v):
    penalty = 0.0
    if "?" in v["rosname"]:
        penalty += 0.5
    elif u["rosname"] != v["rosname"]:
        penalty += 1.0
    return penalty

def cmp_node_ext(u, v):
    penalty = 0.0
    if "?" in v["node_type"]:
        penalty += 0.5
    elif u["node_type"] != v["node_type"]:
        penalty += 1.0
    if u["args"] != v["args"]:
        penalty += 1.0
    if u["conditional"] != v["conditional"]:
        penalty += 1.0
    penalty += cmp_traceability(u["traceability"], v["traceability"])
    return penalty

def cmp_topic_ext(u, v):
    penalty = 0.0
    if u["conditional"] != v["conditional"]:
        penalty += 1.0
    penalty += cmp_traceability_list(u["traceability"], v["traceability"])
    return penalty

def cmp_service_ext(u, v):
    penalty = 0.0
    if u["conditional"] != v["conditional"]:
        penalty += 1.0
    penalty += cmp_traceability_list(u["traceability"], v["traceability"])
    return penalty

def cmp_param_ext(u, v):
    penalty = 0.0
    if u["default_value"] != v["default_value"]:
        penalty += 1.0
    if u["conditional"] != v["conditional"]:
        penalty += 1.0
    penalty += cmp_traceability_list(u["traceability"], v["traceability"])
    return penalty


###############################################################################
# GED Edge Cost Functions
###############################################################################

# edge_subst_cost(G1[u1][v1], G2[u2][v2])
# edge_del_cost(G1[u1][v1])
# edge_ins_cost(G2[u2][v2])

def edge_subst_cost(a, b):
    # receives the edge attribute dictionaries as inputs
    # a: graph edge from ground truth
    # b: graph edge from extracted model
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    if a["link_type"] != b["link_type"]:
        return 1.0
    n = len(b)
    if n == 1:
        return 0.0
    total = float(n - 1) # ignore 'link_type'
    score = total # start with everything right and apply penalties
    score -= cmp_link(a, b)
    if a["link_type"] == PUBLISH or a["link_type"] == SUBSCRIBE:
        score -= cmp_pubsub_ext(a, b)
    elif a["link_type"] == SERVER or a["link_type"] == CLIENT:
        score -= cmp_srvcli_ext(a, b)
    else:
        assert a["link_type"] == GET or a["link_type"] == SET
        score -= cmp_getset_ext(a, b)
    score = (total - score) / total # normalize
    assert score >= 0.0 and score <= 1.0
    return score

def cmp_link(a, b):
    penalty = 0.0
    if "?" in v["rosname"]:
        penalty += 0.5
    elif u["rosname"] != v["rosname"]:
        penalty += 1.0
    if a["conditional"] != b["conditional"]:
        penalty += 1.0
    penalty += cmp_traceability(a["traceability"], b["traceability"])
    return penalty

def cmp_pubsub_ext(a, b):
    penalty = 0.0
    if a["queue_size"] != b["queue_size"]:
        penalty += 1.0
    if a["msg_type"] != b["msg_type"]:
        penalty += 1.0
    return penalty

def cmp_srvcli_ext(a, b):
    penalty = 0.0
    if a["srv_type"] != b["srv_type"]:
        penalty += 1.0
    return penalty

def cmp_getset_ext(a, b):
    penalty = 0.0
    if a["param_type"] != b["param_type"]:
        penalty += 1.0
    return penalty


###############################################################################
# GED Cost Helper Functions
###############################################################################

def cmp_traceability_list(t1, t2):
    assert len(t1) > 0
    if not t2:
        return 1.0
    pd1 = loc_list_to_dict(t1) # package -> file -> {line}
    pd2 = loc_list_to_dict(t2) # package -> file -> {line}
    n_pkg = 0 # expected packages
    p_pkg = 0 # predicted packages
    s_pkg = 0 # spurious packages
    n_file = 0 # expected files
    p_file = 0 # predicted files
    s_file = 0 # spurious files
    n_line = 0 # expected lines
    p_line = 0 # predicted lines
    s_line = 0 # spurious lines
    # calculate predictions
    for p, fd1 in pd1.items():
        n_pkg += 1
        fd2 = pd2.get(p)
        if fd2 is None:
            continue
        p_pkg += 1
        for f, ls1 in fd1.items():
            n_file += 1
            ls2 = fd2.get(f)
            if ls2 is None:
                continue
            p_file += 1
            for l in ls1:
                n_line += 1
                if l in ls2:
                    p_line += 1
    # calculate spurious
    for p, fd2 in pd2.items():
        fd1 = pd1.get(p)
        if fd1 is None:
            s_pkg += 1
            continue
        for f, ls2 in fd2.items():
            ls1 = fd1.get(f)
            if ls1 is None:
                s_file += 1
                continue
            for l in ls2:
                if l not in ls1:
                    s_line += 1
    # F1 measures for package, file and line
    x = f1(n_pkg, p_pkg, s_pkg)
    y = f1(n_file, p_file, s_file)
    z = f1(n_line, p_line, s_line)
    # F1 for packages > F1 for files > F1 for lines
    penalty = (x+x+x + y+y + z) / 6.0
    assert penalty >= 0.0 and penalty <= 1.0
    return penalty

def loc_list_to_dict(locs):
    pd = {}
    for loc in locs:
        p = loc["package"]
        f = loc["file"]
        l = loc["line"]
        if p is None:
            continue
        if p not in pd:
            pd[p] = {}
        if f is None:
            continue
        fd = pd[p]
        if f not in fd:
            fd[f] = set()
        if l is None:
            continue
        fd[f].add(l)
    return pd

def f1(expected, predicted, spurious):
    p = predicted / float(predicted + spurious)
    r = predicted / float(expected)
    if p + r == 0.0:
        return 0.0
    return (2.0 * p * r) / (p + r)


def cmp_traceability(t1, t2):
    # returns the penalty for a source location
    assert t1 is not None
    if t2 is None or t2["package"] != t1["package"]:
        return 1.0
    if t2["file"] != t1["file"]:
        return 0.5
    if t2["line"] != t1["line"]:
        return 1.0 / 6.0
    return 0.0

