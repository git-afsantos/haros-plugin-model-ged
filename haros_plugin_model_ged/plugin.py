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

from builtins import range
from collections import namedtuple

import networkx as nx

###############################################################################
# Constants
###############################################################################

NODE = 1
TOPIC = 2
SERVICE = 3
PARAMETER = 4

RTYPES = {
    NODE: "node",
    TOPIC: "topic",
    SERVICE: "service",
    PARAMETER: "parameter"
}

PUBLISH = 1
SUBSCRIBE = 2
SERVER = 3
CLIENT = 4
GET = 5
SET = 6

LTYPES = {
    PUBLISH: "topic publisher",
    SUBSCRIBE: "topic subscriber",
    SERVER: "service server",
    CLIENT: "service client",
    GET: "parameter reader",
    SET: "parameter writer"
}

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
    f_ged = calc_ged(truth, model)
    paths, cost = calc_edit_paths(truth, model)
    iface.report_metric("simpleGED", s_ged)
    iface.report_metric("fullGED", f_ged)
    iface.report_runtime_violation("reportGED",
        ("Simple GED: {}, Full GED: {}, N: {}, Es: {}, Ef: {}"
         "; Edit Path Cost: {}").format(
            s_ged, f_ged, n, s_ged / n, f_ged / n, cost))
    diff = diff_from_paths(paths, truth, model)
    write_output("ged-output.txt", truth, model, paths, diff)
    iface.export_file("ged-output.txt")


###############################################################################
# Graph Node Attributes
###############################################################################

def location_attrs(loc):
    attrs = {"package": None, "file": None, "line": None}
    if loc is not None:
        if loc.package is not None:
            attrs["package"] = loc.package.name
        if loc.file is not None:
            attrs["file"] = loc.file.full_name
        if loc.line is not None:
            attrs["line"] = loc.line
    return attrs


def node_attrs(node, ext=False):
    attrs = {
        "resource_type": NODE,
        "rosname": node.rosname.full,
        # "rosname": node.rosname.own,
        # "namespace": node.rosname.namespace
    }
    if ext:
        attrs.update({
            "node_type": node.node.node_name,
            "args": node.argv,
            "conditional": bool(node.conditions),
            "traceability": location_attrs(node.traceability()[0])
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
            "traceability": [
                location_attrs(loc) for loc in topic.traceability()]
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
            "traceability": [
                location_attrs(loc) for loc in service.traceability()]
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
            "traceability": [
                location_attrs(loc) for loc in param.traceability()]
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
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": location_attrs(link.source_location),
            "queue_size": link.queue_size,
            "msg_type": link.type
        })
    return attrs

def srvlink_attrs(link, t, ext=False):
    attrs = {
        "link_type": t,
    }
    if ext:
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": location_attrs(link.source_location),
            "srv_type": link.type
        })
    return attrs

def paramlink_attrs(link, t, ext=False):
    attrs = {
        "link_type": t,
    }
    if ext:
        attrs.update({
            "rosname": link.rosname.full,
            # "rosname": link.rosname.own,
            # "namespace": link.rosname.namespace,
            "conditional": bool(link.conditions),
            "traceability": location_attrs(link.source_location),
            "param_type": link.type
        })
    return attrs


###############################################################################
# HAROS to NetworkX Conversion
###############################################################################

def config_to_nx(config, ext=False):
    objs = {}
    G = nx.MultiDiGraph()
    for node in config.nodes.enabled:
        attrs = node_attrs(node, ext=ext)
        uid = "[N{}]{}".format(len(G), attrs["rosname"])
        objs[node] = uid
        G.add_node(uid, **attrs)
    for topic in config.topics.enabled:
        attrs = topic_attrs(topic, ext=ext)
        uid = "[T{}]{}".format(len(G), attrs["rosname"])
        objs[topic] = uid
        G.add_node(uid, **attrs)
    for service in config.services.enabled:
        attrs = service_attrs(service, ext=ext)
        uid = "[S{}]{}".format(len(G), attrs["rosname"])
        objs[service] = uid
        G.add_node(uid, **attrs)
    for param in config.parameters.enabled:
        attrs = param_attrs(param, ext=ext)
        uid = "[P{}]{}".format(len(G), attrs["rosname"])
        objs[param] = uid
        G.add_node(uid, **attrs)
    for node in config.nodes.enabled:
        for link in node.publishers:
            attrs = topiclink_attrs(link, PUBLISH, ext=ext)
            s = objs[link.node]
            t = objs[link.topic]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
        for link in node.subscribers:
            attrs = topiclink_attrs(link, SUBSCRIBE, ext=ext)
            s = objs[link.topic]
            t = objs[link.node]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
        for link in node.servers:
            attrs = srvlink_attrs(link, SERVICE, ext=ext)
            s = objs[link.service]
            t = objs[link.node]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
        for link in node.clients:
            attrs = srvlink_attrs(link, CLIENT, ext=ext)
            s = objs[link.node]
            t = objs[link.service]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
        for link in node.reads:
            attrs = paramlink_attrs(link, GET, ext=ext)
            s = objs[link.parameter]
            t = objs[link.node]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
        for link in node.writes:
            attrs = paramlink_attrs(link, SET, ext=ext)
            s = objs[link.node]
            t = objs[link.parameter]
            uid = "{} -> {}".format(s, t)
            G.add_edge(s, t, key=uid, **attrs)
    return G


###############################################################################
# Ground Truth to NetworkX Conversion
###############################################################################

def truth_to_nx(truth):
    G = nx.MultiDiGraph()
    launch = truth.get("launch")
    if launch:
        truth_launch_to_nx(launch, G)
    links = truth.get("links")
    if links:
        truth_msg_links_to_nx(links, G)
        truth_srv_links_to_nx(links, G)
        truth_param_links_to_nx(links, G)
    return G

def truth_launch_to_nx(launch, G):
    for node in launch.get("nodes", ()):
        attrs = dict(node)
        uid = "[N]" + attrs["rosname"]
        attrs["resource_type"] = NODE
        G.add_node(uid, **attrs)
    for param in launch.get("parameters", ()):
        attrs = dict(param)
        uid = "[P]" + attrs["rosname"]
        attrs["resource_type"] = PARAMETER
        G.add_node(uid, **attrs)

def truth_msg_links_to_nx(links, G):
    for link in links.get("publishers", ()):
        topic_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[T]" + link["topic"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["topic"]
        attrs["link_type"] = PUBLISH
        G.add_edge(s, t, key=uid, **attrs)
    for link in links.get("subscribers", ()):
        topic_from_link(link, G)
        s = "[T]" + link["topic"]
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["topic"]
        attrs["link_type"] = SUBSCRIBE
        G.add_edge(s, t, key=uid, **attrs)

def truth_srv_links_to_nx(links, G):
    for link in links.get("clients", ()):
        service_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[S]" + link["service"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["service"]
        attrs["link_type"] = CLIENT
        G.add_edge(s, t, key=uid, **attrs)
    for link in links.get("servers", ()):
        service_from_link(link, G)
        s = "[S]" + link["service"]
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["service"]
        attrs["link_type"] = SERVER
        G.add_edge(s, t, key=uid, **attrs)

def truth_param_links_to_nx(links, G):
    for link in links.get("sets", ()):
        param_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[P]" + link["parameter"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["parameter"]
        attrs["link_type"] = SET
        G.add_edge(s, t, key=uid, **attrs)
    for link in links.get("gets", ()):
        param_from_link(link, G)
        s = "[P]" + link["parameter"]
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        attrs = dict(link)
        del attrs["node"]
        del attrs["parameter"]
        attrs["link_type"] = GET
        G.add_edge(s, t, key=uid, **attrs)


def topic_from_link(link, G):
    rosname = link["topic"]
    uid = "[T]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        attrs = {
            "resource_type": TOPIC,
            "rosname": rosname,
            "conditional": False,
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditional"] = attrs["conditional"] or link["conditional"]
    attrs["traceability"].append(link["traceability"])

def service_from_link(link, G):
    rosname = link["service"]
    uid = "[S]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        attrs = {
            "resource_type": SERVICE,
            "rosname": rosname,
            "conditional": False,
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditional"] = attrs["conditional"] or link["conditional"]
    attrs["traceability"].append(link["traceability"])

def param_from_link(link, G):
    rosname = link["parameter"]
    uid = "[P]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        attrs = {
            "resource_type": PARAMETER,
            "rosname": rosname,
            "default_value": None,
            "conditional": False,
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditional"] = attrs["conditional"] or link["conditional"]
    attrs["traceability"].append(link["traceability"])


###############################################################################
# Graph Edit Distance Calculation
###############################################################################

def calc_ged(G1, G2):
    return nx.graph_edit_distance(G1, G2,
        node_subst_cost=node_subst_cost,
        node_del_cost=None, # defaults to 1
        node_ins_cost=None, # defaults to 1
        edge_subst_cost=edge_subst_cost,
        edge_del_cost=None, # defaults to 1
        edge_ins_cost=None) # defaults to 1

def calc_edit_paths(G1, G2):
    return nx.optimal_edit_paths(G1, G2,
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

def node_subst_cost(u, v, diff=False):
    # u: graph node from ground truth
    # v: graph node from extracted model
    # should be the dict attributes for each node
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    if u["resource_type"] != v["resource_type"]:
        return 2.0
    d = []
    n = len(v)
    assert n >= 2, str(v)
    total = float(n - 1) # ignore 'resource_type'
    score = total # start with everything right and apply penalties
    score -= cmp_resource(u, v, d)
    if n > 2:
        if u["resource_type"] == NODE:
            score -= cmp_node_ext(u, v, d)
        elif u["resource_type"] == TOPIC:
            score -= cmp_topic_ext(u, v, d)
        elif u["resource_type"] == SERVICE:
            score -= cmp_service_ext(u, v, d)
        else:
            assert u["resource_type"] == PARAMETER
            score -= cmp_param_ext(u, v, d)
    score = (total - score) / total # normalize
    assert score >= 0.0 and score <= 1.0
    if diff:
        return score, d
    return score


def cmp_resource(u, v, d):
    penalty = 0.0
    udata = u["rosname"]
    vdata = v["rosname"]
    if "?" in vdata:
        penalty += 0.5
        d.append(("rosname", udata, vdata))
    elif udata != vdata:
        penalty += 1.0
        d.append(("rosname", udata, vdata))
    return penalty

def cmp_node_ext(u, v, d):
    penalty = 0.0
    udata = u["node_type"]
    vdata = v["node_type"]
    if "?" in vdata:
        penalty += 0.5
        d.append(("node_type", udata, vdata))
    elif udata != vdata:
        penalty += 1.0
        d.append(("node_type", udata, vdata))
    udata = u["args"]
    vdata = v["args"]
    if udata != vdata:
        penalty += 1.0
        d.append(("args", udata, vdata))
    udata = u["conditional"]
    vdata = v["conditional"]
    if udata != vdata:
        penalty += 1.0
        d.append(("conditional", udata, vdata))
    penalty += cmp_traceability(u["traceability"], v["traceability"], d)
    return penalty

def cmp_topic_ext(u, v, d):
    penalty = 0.0
    udata = u["conditional"]
    vdata = v["conditional"]
    if udata != vdata:
        penalty += 1.0
        d.append(("conditional", udata, vdata))
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty

def cmp_service_ext(u, v, d):
    penalty = 0.0
    udata = u["conditional"]
    vdata = v["conditional"]
    if udata != vdata:
        penalty += 1.0
        d.append(("conditional", udata, vdata))
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty

def cmp_param_ext(u, v, d):
    penalty = 0.0
    udata = u["default_value"]
    vdata = v["default_value"]
    if udata != vdata:
        penalty += 1.0
        d.append(("default_value", udata, vdata))
    udata = u["conditional"]
    vdata = v["conditional"]
    if udata != vdata:
        penalty += 1.0
        d.append(("conditional", udata, vdata))
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty


###############################################################################
# GED Edge Cost Functions
###############################################################################

# edge_subst_cost(G1[u1][v1], G2[u2][v2])
# edge_del_cost(G1[u1][v1])
# edge_ins_cost(G2[u2][v2])

def edge_subst_cost(a, b, diff=False):
    # receives the edge attribute dictionaries as inputs
    # a: graph edge from ground truth
    # b: graph edge from extracted model
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    if a["link_type"] != b["link_type"]:
        return 2.0
    d = []
    n = len(b)
    if n == 1:
        return 0.0
    total = float(n - 1) # ignore 'link_type'
    score = total # start with everything right and apply penalties
    score -= cmp_link(a, b, d)
    if a["link_type"] == PUBLISH or a["link_type"] == SUBSCRIBE:
        score -= cmp_pubsub_ext(a, b, d)
    elif a["link_type"] == SERVER or a["link_type"] == CLIENT:
        score -= cmp_srvcli_ext(a, b, d)
    else:
        assert a["link_type"] == GET or a["link_type"] == SET
        score -= cmp_getset_ext(a, b, d)
    score = (total - score) / total # normalize
    assert score >= 0.0 and score <= 1.0
    if diff:
        return score, d
    return score

def cmp_link(a, b, d):
    penalty = 0.0
    adata = a["rosname"]
    bdata = b["rosname"]
    if "?" in bdata:
        penalty += 0.5
        d.append(("rosname", adata, bdata))
    elif adata != bdata:
        penalty += 1.0
        d.append(("rosname", adata, bdata))
    adata = a["conditional"]
    bdata = b["conditional"]
    if adata != bdata:
        penalty += 1.0
        d.append(("conditional", adata, bdata))
    penalty += cmp_traceability(a["traceability"], b["traceability"], d)
    return penalty

def cmp_pubsub_ext(a, b, d):
    penalty = 0.0
    adata = a["queue_size"]
    bdata = b["queue_size"]
    if adata != bdata:
        penalty += 1.0
        d.append(("queue_size", adata, bdata))
    adata = a["msg_type"]
    bdata = b["msg_type"]
    if adata != bdata:
        penalty += 1.0
        d.append(("msg_type", adata, bdata))
    return penalty

def cmp_srvcli_ext(a, b, d):
    penalty = 0.0
    adata = a["srv_type"]
    bdata = b["srv_type"]
    if adata != bdata:
        penalty += 1.0
        d.append(("srv_type", adata, bdata))
    return penalty

def cmp_getset_ext(a, b, d):
    penalty = 0.0
    adata = a["param_type"]
    bdata = b["param_type"]
    if adata != bdata:
        penalty += 1.0
        d.append(("param_type", adata, bdata))
    return penalty


###############################################################################
# GED Cost Helper Functions
###############################################################################

def cmp_traceability_list(t1, t2, d):
    assert len(t1) > 0
    if not t2:
        return 1.0
    pd1 = loc_list_to_dict(t1) # package -> file -> {line}
    pd2 = loc_list_to_dict(t2) # package -> file -> {line}
    # expected, predicted, spurious packages
    n_pkg = p_pkg = s_pkg = 0
    # expected, predicted, spurious files
    n_file = p_file = s_file = 0
    # expected, predicted, spurious lines
    n_line = p_line = s_line = 0
    # calculate predictions
    for p, fd1 in pd1.items():
        n_pkg += 1
        fd2 = pd2.get(p)
        if fd2 is None:
            # ---- begin reporting ----
            for f, ls1 in fd1.items():
                for l in ls1:
                    d.append(("traceability", (p, f, l), None))
            # ---- end reporting ----
            continue
        p_pkg += 1
        _f = (p, None, None)
        for f, ls1 in fd1.items():
            n_file += 1
            ls2 = fd2.get(f)
            if ls2 is None:
                # ---- begin reporting ----
                for l in ls1:
                    d.append(("traceability", (p, f, l), _f))
                # ---- end reporting ----
                continue
            p_file += 1
            _f = (p, f, None)
            for l in ls1:
                n_line += 1
                if l in ls2:
                    p_line += 1
                else:
                    # ---- begin reporting ----
                    d.append(("traceability", (p, f, l), _f))
                    # ---- end reporting ----
    # calculate spurious
    for p, fd2 in pd2.items():
        fd1 = pd1.get(p)
        if fd1 is None:
            # ---- begin reporting ----
            for f, ls2 in fd2.items():
                for l in ls2:
                    d.append(("traceability", None, (p, f, l)))
            # ---- end reporting ----
            s_pkg += 1
            continue
        for f, ls2 in fd2.items():
            ls1 = fd1.get(f)
            if ls1 is None:
                # ---- begin reporting ----
                for l in ls2:
                    d.append(("traceability", None, (p, f, l)))
                # ---- end reporting ----
                s_file += 1
                continue
            for l in ls2:
                if l not in ls1:
                    # ---- begin reporting ----
                    d.append(("traceability", None, (p, f, l)))
                    # ---- end reporting ----
                    s_line += 1
    # F1 measures for package, file and line
    x = f1(n_pkg, p_pkg, s_pkg)
    y = f1(n_file, p_file, s_file)
    z = f1(n_line, p_line, s_line)
    # F1 for packages > F1 for files > F1 for lines
    penalty = 1.0 - (x+x+x + y+y + z) / 6.0
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
    if expected == 0:
        return 1.0
    if predicted == 0 and spurious == 0:
        return 0.0
    p = predicted / float(predicted + spurious)
    r = predicted / float(expected)
    if p + r == 0.0:
        return 0.0
    return (2.0 * p * r) / (p + r)


def cmp_traceability(t1, t2, d):
    # returns the penalty for a source location
    assert t1 is not None
    _t = (t1["package"], t1["file"], t1["line"])
    if t2 is None:
        d.append(("traceability", _t, t2))
        return 1.0
    _f = (t2["package"], t2["file"], t2["line"])
    if _t[0] != _f[0]:
        d.append(("traceability", _t, _f))
        return 1.0
    if _t[1] != _f[1]:
        d.append(("traceability", _t, _f))
        return 0.5
    if _t[2] != _f[2]:
        d.append(("traceability", _t, _f))
        return 1.0 / 6.0
    return 0.0


###############################################################################
# Diff Calculation
###############################################################################

Diff = namedtuple("Diff", (
    "partial_nodes",
    "missed_nodes",
    "spurious_nodes",
    "partial_edges", 
    "missed_edges",
    "spurious_edges"
))

def _new_diff():
    return Diff([], [], [], [], [], [])

def diff_from_paths(paths, truth, model):
    diff = _new_diff()
    for node_list, edge_list in paths:
        for u, v in node_list:
            assert not (u is None and v is None)
            if u is None:
                d = model.nodes[v]
                t = RTYPES[d["resource_type"]]
                diff.spurious_nodes.append((t, v))
            elif v is None:
                d = truth.nodes[u]
                t = RTYPES[d["resource_type"]]
                diff.missed_nodes.append((t, u))
            else:
                _, d = node_subst_cost(truth.nodes[u], model.nodes[v], diff=True)
                if d:
                    t = RTYPES[truth.nodes[u]["resource_type"]]
                    diff.partial_nodes.append((t, u, v, d))
        for a, b in edge_list:
            assert not (a is None and b is None)
            if a is None:
                d = model.edges[b]
                t = LTYPES[d["link_type"]]
                diff.spurious_edges.append((t, b[2]))
            elif b is None:
                d = truth.edges[a]
                t = LTYPES[d["link_type"]]
                diff.missed_edges.append((t, a[2]))
            else:
                e1 = truth.edges[a]
                e2 = model.edges[b]
                _, d = edge_subst_cost(e1, e2, diff=True)
                if d:
                    t = LTYPES[e1["link_type"]]
                    diff.partial_edges.append((t, a[2], b[2], d))
    return diff


###############################################################################
# Formatting
###############################################################################

def write_output(fname, truth, model, paths, diff):
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
