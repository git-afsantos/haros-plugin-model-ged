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

from builtins import range
from collections import namedtuple
import re

import networkx as nx
from networkx.algorithms import bipartite


###############################################################################
# Helper Classes
###############################################################################

GraphData = namedtuple("GraphData",
    ("nodes", "parameters", "publishers", "subscribers",
     "clients", "servers", "setters", "getters"))

NodeAttrs = namedtuple("NodeAttrs",
    ("key", "rosname", "rostype", "traceability", "args", "conditions"))

ParamAttrs = namedtuple("ParamAttrs",
    ("key", "rosname", "rostype", "traceability", "value", "conditions"))

PubAttrs = namedtuple("PubAttrs",
    ("key", "node", "rosname", "rostype", "traceability", "original_name",
     "queue_size", "latched", "conditions"))

SubAttrs = namedtuple("SubAttrs",
    ("key", "node", "rosname", "rostype", "traceability", "original_name",
     "queue_size", "conditions"))

CliAttrs = namedtuple("CliSrvAttrs",
    ("key", "node", "rosname", "rostype", "traceability", "original_name",
     "conditions"))

SrvAttrs = CliAttrs

SetAttrs = namedtuple("SetGetAttrs",
    ("key", "node", "rosname", "rostype", "traceability", "original_name",
     "value", "conditions"))

GetAttrs = SetAttrs


Guard = namedtuple("Guard",
    ("package", "file", "line", "column", "statement", "condition"))

Location = namedtuple("Location", ("package", "file", "line", "column"))

Matching = namedtuple("Matching", ("matched", "missed", "spurious"))


###############################################################################
# Graph Matching
###############################################################################

def matching_by_name(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_rosname,
        cost_param=cost_rosname,
        cost_pub=cost_link_rosname,
        cost_sub=cost_link_rosname,
        cost_cli=cost_link_rosname,
        cost_srv=cost_link_rosname,
        cost_set=cost_link_rosname,
        cost_get=cost_link_rosname)

def matching_by_name_type(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_rosname_rostype,
        cost_param=cost_rosname_rostype,
        cost_pub=cost_link_rosname_rostype,
        cost_sub=cost_link_rosname_rostype,
        cost_cli=cost_link_rosname_rostype,
        cost_srv=cost_link_rosname_rostype,
        cost_set=cost_link_rosname_rostype,
        cost_get=cost_link_rosname_rostype)

def matching_by_name_type_loc(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_rosname_rostype_traceability,
        cost_param=cost_rosname_rostype_traceability,
        cost_pub=cost_link_rosname_rostype_traceability,
        cost_sub=cost_link_rosname_rostype_traceability,
        cost_cli=cost_link_rosname_rostype_traceability,
        cost_srv=cost_link_rosname_rostype_traceability,
        cost_set=cost_link_rosname_rostype_traceability,
        cost_get=cost_link_rosname_rostype_traceability)

def matching_by_loc(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_traceability_main,
        cost_param=cost_traceability_main,
        cost_pub=cost_traceability_main,
        cost_sub=cost_traceability_main,
        cost_cli=cost_traceability_main,
        cost_srv=cost_traceability_main,
        cost_set=cost_traceability_main,
        cost_get=cost_traceability_main)

def matching_by_loc_name(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_traceability_rosname,
        cost_param=cost_traceability_rosname,
        cost_pub=cost_traceability_link_rosname,
        cost_sub=cost_traceability_link_rosname,
        cost_cli=cost_traceability_link_rosname,
        cost_srv=cost_traceability_link_rosname,
        cost_set=cost_traceability_link_rosname,
        cost_get=cost_traceability_link_rosname)

def matching_by_loc_name_type(config, truth):
    return calc_matching(config, truth,
        cost_node=cost_traceability_rosname_rostype,
        cost_param=cost_traceability_rosname_rostype,
        cost_pub=cost_traceability_link_rosname_rostype,
        cost_sub=cost_traceability_link_rosname_rostype,
        cost_cli=cost_traceability_link_rosname_rostype,
        cost_srv=cost_traceability_link_rosname_rostype,
        cost_set=cost_traceability_link_rosname_rostype,
        cost_get=cost_traceability_link_rosname_rostype)


def calc_matching(config, truth, cost_node=None, cost_param=None,
        cost_pub=None, cost_sub=None, cost_cli=None, cost_srv=None,
        cost_set=None, cost_get=None):
    m1 = node_matching(config.nodes.enabled,
        truth["launch"]["nodes"], cost_node)
    m2 = param_matching(config.parameters.enabled,
        truth["launch"]["parameters"], cost_param)
    m3 = pub_matching(config.topics.enabled,
        truth["links"]["publishers"], cost_pub)
    m4 = sub_matching(config.topics.enabled,
        truth["links"]["subscribers"], cost_sub)
    m5 = cli_matching(config.services.enabled,
        truth["links"]["clients"], cost_cli)
    m6 = srv_matching(config.services.enabled,
        truth["links"]["servers"], cost_srv)
    m7 = setter_matching(config.parameters.enabled,
        truth["links"]["setters"], cost_set)
    m8 = getter_matching(config.parameters.enabled,
        truth["links"]["getters"], cost_get)
    return GraphData(m1, m2, m3, m4, m5, m6, m7, m8)


###############################################################################
# Matching Functions
###############################################################################

def node_matching(config_nodes, truth_nodes, cf):
    i = 1
    lhs = []
    rhs = []
    for node in config_nodes:
        lhs.append(convert_haros_node(i, node))
        i += 1
    for rosname, data in truth_nodes.items():
        rhs.append(convert_truth_node(i, rosname, data))
        i += 1
    return _matching(lhs, rhs, cf)

def param_matching(config_params, truth_params, cf):
    i = 1
    lhs = []
    rhs = []
    for param in config_params:
        if not param.launch:
            continue
        lhs.append(convert_haros_param(i, param))
        i += 1
    for rosname, data in truth_params.items():
        rhs.append(convert_truth_param(i, rosname, data))
        i += 1
    return _matching(lhs, rhs, cf)

def pub_matching(config_topics, truth_pubs, cf):
    i = 1
    lhs = []
    rhs = []
    for topic in config_topics:
        for link in topic.publishers:
            lhs.append(convert_haros_pub(i, link))
            i += 1
    for link in truth_pubs:
        rhs.append(convert_truth_pub(i, link))
        i += 1
    return _matching(lhs, rhs, cf)

def sub_matching(config_topics, truth_subs, cf):
    i = 1
    lhs = []
    rhs = []
    for topic in config_topics:
        for link in topic.subscribers:
            lhs.append(convert_haros_sub(i, link))
            i += 1
    for link in truth_subs:
        rhs.append(convert_truth_sub(i, link))
        i += 1
    return _matching(lhs, rhs, cf)

def cli_matching(config_services, truth_clients, cf):
    i = 1
    lhs = []
    rhs = []
    for service in config_services:
        for link in service.clients:
            lhs.append(convert_haros_cli(i, link))
            i += 1
    for link in truth_clients:
        rhs.append(convert_truth_cli(i, link))
        i += 1
    return _matching(lhs, rhs, cf)

def srv_matching(config_services, truth_servers, cf):
    i = 1
    lhs = []
    rhs = []
    for service in config_services:
        if service.server is not None:
            lhs.append(convert_haros_srv(i, service.server))
            i += 1
    for link in truth_servers:
        rhs.append(convert_truth_srv(i, link))
        i += 1
    return _matching(lhs, rhs, cf)

def setter_matching(config_params, truth_setters, cf):
    i = 1
    lhs = []
    rhs = []
    for param in config_params:
        for link in param.writes:
            lhs.append(convert_haros_setter(i, link))
            i += 1
    for link in truth_setters:
        rhs.append(convert_truth_setter(i, link))
        i += 1
    return _matching(lhs, rhs, cf)

def getter_matching(config_params, truth_getters, cf):
    i = 1
    lhs = []
    rhs = []
    for param in config_params:
        for link in param.reads:
            lhs.append(convert_haros_getter(i, link))
            i += 1
    for link in truth_getters:
        rhs.append(convert_truth_getter(i, link))
        i += 1
    return _matching(lhs, rhs, cf)


def _matching(lhs, rhs, cf):
    G = nx.Graph()
    top = []
    for v in rhs:
        G.add_node(v.key, data=v, bipartite=1)
        top.append(v.key)
    for u in lhs:
        G.add_node(u.key, data=u, bipartite=0)
        for v in rhs:
            weight = cf(u, v)
            G.add_edge(u, v, weight=weight)
    M = bipartite.matching.minimum_weight_full_matching(G, top_nodes=top)
    # The matching is returned as a dictionary such that
    #   M[u] == v if node u is matched to node v.
    # Unmatched nodes do not occur as a key.
    matched = []
    missed = []
    spurious = []
    for u in lhs:
        v = M.get(u.key)
        if v is None:
            spurious.append(u)
        else:
            matched.append((u, v))
    for v in rhs:
        if v.key not in M:
            missed.append(v)
    return Matching(matched, missed, spurious)


###############################################################################
# Cost Functions
###############################################################################

# '/?/?' means both namespace and own name are unknown
# '/?' means the global namespace with own name unknown
def _cost_rosname(predicted, gold):
    if predicted == gold:
        return 0
    if "?" in predicted:
        p = name_pattern(predicted)
        if p.match(gold):
            return 1
    return 2

def cost_rosname(u, v):
    return _cost_rosname(u.rosname, v.rosname)

def cost_link_rosname(u, v):
    return _cost_rosname(u.node, v.node) + _cost_rosname(u.rosname, v.rosname)


def _cost_rostype(predicted, gold):
    if predicted == gold:
        return 0
    if predicted is None or "?" in predicted:
        return 1
    return 2

def cost_rostype(u, v):
    if u.rostype == v.rostype:
        return 0
    if u.rostype is None or "?" in u.rostype:
        return 1
    return 2


def cost_rosname_rostype(u, v):
    return 10 * cost_rosname(u, v) + cost_rostype(u, v)

def cost_link_rosname_rostype(u, v):
    return 10 * cost_link_rosname(u, v) + cost_rostype(u, v)


def cost_traceability(u, v):
    p = u.traceability
    g = v.traceability
    assert g.package is not None
    assert g.file is not None
    assert g.line is not None
    assert g.column is not None
    if p.package != g.package:
        return 4
    if p.file != g.file:
        return 3
    if p.line != g.line:
        return 2
    if p.column != g.column:
        return 1
    return 0


def cost_rosname_rostype_traceability(u, v):
    cost = 100 * cost_rosname(u, v) + 10 * cost_rostype(u, v)
    return cost + cost_traceability(u, v)

def cost_link_rosname_rostype_traceability(u, v):
    cost = 100 * cost_link_rosname(u, v) + 10 * cost_rostype(u, v)
    return cost + cost_traceability(u, v)


def cost_traceability_main(u, v):
    p = u.traceability
    g = v.traceability
    assert g.package is not None
    assert g.file is not None
    assert g.line is not None
    assert g.column is not None
    if p.package is None:
        return 8
    if p.package != g.package:
        return 8
    if p.file is None:
        return 4
    if p.file != g.file:
        return 4
    if p.line is None or p.column is None:
        return 3
    d_line = int(abs(g.line - p.line))
    d_col = int(abs(g.column - p.column))
    if d_line > 0:
        if d_line == 1:
            if not d_col:
                return 1
            return 2
        return 3
    elif d_col > 0:
        assert d_col > 0
        if d_col <= 8:
            return 1
        if d_col < 50:
            return 2
        return 3
    return 0


def cost_traceability_rosname(u, v):
    cost = 10 * cost_traceability_main(u, v)
    return cost + cost_rosname(u, v)

def cost_traceability_link_rosname(u, v):
    cost = 10 * cost_traceability_main(u, v)
    return cost + cost_link_rosname(u, v)


def cost_traceability_rosname_rostype(u, v):
    cost = 100 * cost_traceability_main(u, v)
    cost += 10 * cost_rosname(u, v)
    return cost + cost_rostype(u, v)

def cost_traceability_link_rosname_rostype(u, v):
    cost = 100 * cost_traceability_main(u, v)
    cost += 10 * cost_link_rosname(u, v)
    return cost + cost_rostype(u, v)


###############################################################################
# HAROS Conversion Functions
###############################################################################

def convert_haros_node(i, node):
    traceability = convert_haros_location(node._location)
    conditions = convert_haros_conditions(node.conditions)
    return NodeAttrs(i, node.id, node.type, traceability, node.argv, conditions)

def convert_haros_param(i, param):
    assert param.launch is not None
    traceability = convert_haros_location(param._location)
    conditions = convert_haros_conditions(param.conditions)
    return ParamAttrs(i, param.id, param.type, traceability, param.value,
                      conditions)

def convert_haros_pub(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return PubAttrs(i, link.node.id, link.topic.id, link.type, traceability,
        link.rosname.full, link.queue_size, False, conditions)

def convert_haros_sub(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return SubAttrs(i, link.node.id, link.topic.id, link.type, traceability,
        link.rosname.full, link.queue_size, conditions)

def convert_haros_cli(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return CliAttrs(i, link.node.id, link.service.id, link.type, traceability,
        link.rosname.full, conditions)

def convert_haros_srv(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return SrvAttrs(i, link.node.id, link.service.id, link.type, traceability,
        link.rosname.full, conditions)

def convert_haros_setter(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return SetAttrs(i, link.node.id, link.parameter.id, link.type, traceability,
        link.rosname.full, None, conditions)

def convert_haros_getter(i, link):
    traceability = convert_haros_location(link.source_location)
    conditions = convert_haros_conditions(link.conditions)
    return GetAttrs(i, link.node.id, link.parameter.id, link.type, traceability,
        link.rosname.full, None, conditions)


def convert_haros_location(loc):
    if loc is None or loc.package is None:
        return Location(None, None, None, None)
    if loc.file is None:
        return Location(loc.package.name, None, None, None)
    return Location(loc.package.name, loc.file.full_name, loc.line, loc.column)

def convert_haros_conditions(conditions):
    cfg = {}
    for condition in conditions:
        loc = convert_haros_location(condition.location)
        g = Guard(loc.package, loc.file, loc.line, loc.column,
                  condition.statement, condition.condition)
        cfg[g] = {}
    return cfg

###############################################################################
# Ground Truth Conversion Functions
###############################################################################

def convert_truth_node(i, rosname, data):
    rostype = data["node_type"]
    traceability = convert_truth_traceability(data["traceability"])
    args = data.get("args", [])
    conditions = convert_truth_conditions(data.get("conditions", ()))
    return NodeAttrs(i, rosname, rostype, traceability, args, conditions)

def convert_truth_param(i, rosname, data):
    rostype = data.get("default_type")
    traceability = convert_truth_traceability(data["traceability"])
    value = data.get("default_value")
    conditions = convert_truth_conditions(data.get("conditions", ()))
    return ParamAttrs(i, rosname, rostype, traceability, value, conditions)

def convert_truth_pub(i, link):
    node = link["node"]
    rosname = link["topic"]
    rostype = link["msg_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    queue_size = link["queue_size"]
    latched = link.get("latched", False)
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return PubAttrs(i, node, rosname, rostype, traceability,
                    original_name, queue_size, latched, conditions)

def convert_truth_sub(i, link):
    node = link["node"]
    rosname = link["topic"]
    rostype = link["msg_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    queue_size = link["queue_size"]
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return SubAttrs(i, node, rosname, rostype, traceability,
                    original_name, queue_size, conditions)

def convert_truth_cli(i, link):
    node = link["node"]
    rosname = link["service"]
    rostype = link["srv_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return CliAttrs(i, node, rosname, rostype, traceability,
                    original_name, conditions)

def convert_truth_srv(i, link):
    node = link["node"]
    rosname = link["service"]
    rostype = link["srv_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return SrvAttrs(i, node, rosname, rostype, traceability,
                    original_name, conditions)

def convert_truth_setter(i, link):
    node = link["node"]
    rosname = link["parameter"]
    rostype = link["param_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    value = link.get("value")
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return SetAttrs(i, node, rosname, rostype, traceability,
                    original_name, value, conditions)

def convert_truth_getter(i, link):
    node = link["node"]
    rosname = link["parameter"]
    rostype = link["param_type"]
    traceability = convert_truth_traceability(link["traceability"])
    original_name = link.get("rosname", rosname)
    value = link.get("default_value")
    conditions = convert_truth_conditions(link.get("conditions", ()))
    return GetAttrs(i, node, rosname, rostype, traceability,
                    original_name, value, conditions)


def convert_truth_traceability(traceability):
    if traceability is None:
        return Location(None, None, None, None)
    return Location(traceability["package"], traceability["file"],
        traceability["line"], traceability["column"])

def convert_truth_conditions(paths):
    cfg = {}
    for path in paths:
        r = cfg
        for c in path:
            g = Guard(c["package"], c["file"], c["line"], c["column"],
                      c["statement"], c["condition"])
            s = r.get(g)
            if s is None:
                s = {}
                r[g] = s
            r = s
    return cfg

###############################################################################
# Helper Functions
###############################################################################

def name_pattern(rosname):
    parts = []
    prev = "/"
    n = len(rosname)
    i = 0
    assert n > 1 and rosname[0] == "/"
    for j in range(1, n):
        if rosname[j] == "?":
            assert prev != "?"
            if prev == "/":
                if j == n - 1: # self._name.endswith("/?")
                    # end, whole part for sure
                    parts.append(rosname[i:j])
                    parts.append("(.+?)")
                elif rosname[j+1] == "/": # "/?/"
                    # start and middle, whole parts
                    parts.append(rosname[i:j-1])
                    parts.append("(/.+?)?")
                else: # "/?a", optional part
                    parts.append(rosname[i:j])
                    parts.append("(.*?)")
            else: # "a?/", "a?a", "/a?", optional part
                parts.append(rosname[i:j])
                parts.append("(.*?)")
            i = j + 1
        prev = rosname[j]
    if i < n:
        parts.append(rosname[i:])
    parts.append("$")
    return re.compile("".join(parts))
