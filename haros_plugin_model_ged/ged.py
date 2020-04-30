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

from bisect import bisect
from builtins import range
from collections import namedtuple

from networkx import graph_edit_distance, optimal_edit_paths

from .haros2nx import (
    NODE, TOPIC, SERVICE, PARAMETER,
    PUBLISHER, SUBSCRIBER, SERVER, CLIENT, GET, SET
)

###############################################################################
# Constants
###############################################################################

# costs of partially correct locations (nothing, just pkg, pkg and file)
COST_LOC_NONE = 1#3
COST_LOC_PKG = 1#2
COST_LOC_FILE = 1

TYPES = {
    NODE: "node",
    TOPIC: "topic",
    SERVICE: "service",
    PARAMETER: "parameter",
    PUBLISHER: "topic publisher",
    SUBSCRIBER: "topic subscriber",
    SERVER: "service server",
    CLIENT: "service client",
    GET: "get parameter",
    SET: "set parameter"
}


###############################################################################
# Graph Edit Distance Calculation
###############################################################################

def calc_ged(G1, G2, ext=False):
    if ext:
        return graph_edit_distance(G1, G2,
            node_subst_cost=node_subst_cost_2,
            node_del_cost=sizeof_node,
            node_ins_cost=sizeof_node,
            edge_subst_cost=edge_subst_cost_2,
            edge_del_cost=sizeof_edge,
            edge_ins_cost=sizeof_edge)
    else:
        return graph_edit_distance(G1, G2,
            node_subst_cost=node_subst_cost_0,
            node_del_cost=None, # defaults to 1
            node_ins_cost=None, # defaults to 1
            edge_subst_cost=edge_subst_cost_0,
            edge_del_cost=None, # defaults to 1
            edge_ins_cost=None) # defaults to 1

def calc_edit_paths(G1, G2, ext=False):
    if ext:
        return optimal_edit_paths(G1, G2,
            node_subst_cost=node_subst_cost_2,
            node_del_cost=sizeof_node,
            node_ins_cost=sizeof_node,
            edge_subst_cost=edge_subst_cost_2,
            edge_del_cost=sizeof_edge,
            edge_ins_cost=sizeof_edge)
    else:
        return optimal_edit_paths(G1, G2,
            node_subst_cost=node_subst_cost_0,
            node_del_cost=None, # defaults to 1
            node_ins_cost=None, # defaults to 1
            edge_subst_cost=edge_subst_cost_0,
            edge_del_cost=None, # defaults to 1
            edge_ins_cost=None) # defaults to 1


###############################################################################
# GED Node Cost Functions
###############################################################################

# node_subst_cost(G1.nodes[n1], G2.nodes[n2])
# node_del_cost(G1.nodes[n1])
# node_ins_cost(G2.nodes[n2])

def impossible_node_subst(u, v):
    return 2 * max(sizeof_node(u), sizeof_node(v)) + 1

def node_subst_cost_0(u, v):
    if u["nxtype"] != v["nxtype"]:
        return impossible_node_subst(u, v)
    udata = u["rosname"]
    vdata = v["rosname"]
    if udata == vdata:
        return 0
    #if "?" in vdata and udata.count("/") == vdata.count("/"):
    return 1

def node_subst_cost_2(u, v, diff=False):
    # u: graph node from ground truth
    # v: graph node from extracted model
    # should be the dict attributes for each node
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    nxtype = u["nxtype"]
    if nxtype != v["nxtype"]:
        return impossible_node_subst(u, v)
    d = [] if diff else NullList()
    cost = cmp_resource(u, v, d)
    if nxtype == NODE:
        cost += cmp_node_ext(u, v, d)
    elif nxtype == TOPIC:
        cost += cmp_topic_ext(u, v, d)
    elif nxtype == SERVICE:
        cost += cmp_service_ext(u, v, d)
    elif nxtype == PARAMETER:
        cost += cmp_param_ext(u, v, d)
    return (cost, d) if diff else cost


def cmp_resource(u, v, d):
    udata = u["rosname"]
    vdata = v["rosname"]
    if udata == vdata:
        return 0
    d.append(("rosname", udata, vdata))
    #if "?" in vdata and udata.count("/") == vdata.count("/"):
    return 1

def cmp_node_ext(u, v, d):
    cost = 0
    udata = u["node_type"]
    vdata = v["node_type"]
    if udata != vdata:
        cost += 1
        d.append(("node_type", udata, vdata))
    udata = u["args"]
    vdata = v["args"]
    if udata != vdata:
        cost += 1
        d.append(("args", udata, vdata))
    cost += cmp_conditions(u["conditions"], v["conditions"], d)
    cost += cmp_traceability(u["traceability"], v["traceability"], d)
    return cost

def cmp_topic_ext(u, v, d):
    cost = cmp_conditions(u["conditions"], v["conditions"], d)
    cost += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return cost

def cmp_service_ext(u, v, d):
    cost = cmp_conditions(u["conditions"], v["conditions"], d)
    cost += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return cost

def cmp_param_ext(u, v, d):
    cost = 0
    udata = u["default_value"]
    vdata = v["default_value"]
    if udata != vdata:
        cost += 1
        d.append(("default_value", udata, vdata))
    cost += cmp_conditions(u["conditions"], v["conditions"], d)
    cost += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return cost


###############################################################################
# GED Edge Cost Functions
###############################################################################

# edge_subst_cost(G1[u1][v1], G2[u2][v2])
# edge_del_cost(G1[u1][v1])
# edge_ins_cost(G2[u2][v2])

def impossible_edge_subst(a, b):
    return 2 * max(sizeof_edge(a), sizeof_edge(b)) + 1

def edge_subst_cost_0(a, b):
    if a["nxtype"] != b["nxtype"]:
        return impossible_edge_subst(a, b)
    return 0

def edge_subst_cost_2(a, b, diff=False):
    # receives the edge attribute dictionaries as inputs
    # a: graph edge from ground truth
    # b: graph edge from extracted model
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    nxtype = a["nxtype"]
    if nxtype != b["nxtype"]:
        return impossible_edge_subst(a, b)
    d = [] if diff else NullList()
    cost = cmp_link(a, b, d)
    if nxtype == PUBLISHER or nxtype == SUBSCRIBER:
        cost += cmp_pubsub_ext(a, b, d)
    elif nxtype == SERVER or nxtype == CLIENT:
        cost += cmp_srvcli_ext(a, b, d)
    elif nxtype == GET or nxtype == SET:
        cost += cmp_getset_ext(a, b, d)
    return (cost, d) if diff else cost

def cmp_link(a, b, d):
    cost = 0
    adata = a["rosname"]
    bdata = b["rosname"]
    if adata != bdata:
        cost += 1
        d.append(("rosname", adata, bdata))
    cost += cmp_conditions(a["conditions"], b["conditions"], d)
    cost += cmp_traceability(a["traceability"], b["traceability"], d)
    return cost

def cmp_pubsub_ext(a, b, d):
    cost = 0
    adata = a["queue_size"]
    bdata = b["queue_size"]
    if adata != bdata:
        cost += 1
        d.append(("queue_size", adata, bdata))
    adata = a["msg_type"]
    bdata = b["msg_type"]
    if adata != bdata:
        cost += 1
        d.append(("msg_type", adata, bdata))
    return cost

def cmp_srvcli_ext(a, b, d):
    cost = 0
    adata = a["srv_type"]
    bdata = b["srv_type"]
    if adata != bdata:
        cost += 1
        d.append(("srv_type", adata, bdata))
    return cost

def cmp_getset_ext(a, b, d):
    cost = 0
    adata = a["param_type"]
    bdata = b["param_type"]
    if adata != bdata:
        cost += 1
        d.append(("param_type", adata, bdata))
    return cost


###############################################################################
# GED Cost Helper Functions
###############################################################################

def cmp_conditions(cfg1, cfg2, d):
    if not cfg1 and cfg2:
        return conditions_size(cfg2)
    if cfg1 and not cfg2:
        return conditions_size(cfg1)
    n = p = s = 0
    queue = [(cfg1, cfg2)]
    while queue:
        new_queue = []
        for c1, c2 in queue:
            for g, child1 in c1.items():
                n += 1
                child2 = c2.get(g)
                if child2 is None:
                    d.append(("conditions", g, None))
                else:
                    p += 1
                    new_queue.append((child1, child2))
            for g, child2 in c2.items():
                child1 = c1.get(g)
                if child1 is None:
                    s += 1
                    d.append(("conditions", None, g))
        queue = new_queue
    return (n - p) + s


def cmp_traceability_list(tl1, tl2, d):
    # None comes before data
    # s = [1,3,5,7,9]
    # bisect(s, 0) == 0
    # bisect(s, 2) == 1
    # bisect(s, 3) == 2
    # bisect(s, 10) == 5
    missed = sorted(tl1)
    n = traceability_list_size(tl1)
    p = s = 0
    bucket1, bucket2, bucket3, bucket4 = location_buckets(tl2)
    for loc in bucket4:
        i = bisect(missed, loc)
        if i > 0 and missed[i-1] == loc:
            p += COST_LOC_NONE
            del missed[i-1]
        else:
            s += COST_LOC_NONE
            d.append(("traceability", None, loc))
    for loc in bucket3:
        i = bisect(missed, loc)
        if i >= len(missed): # no match candidate
            s += COST_LOC_NONE
            d.append(("traceability", None, loc))
        else: # there is a match candidate
            m = missed[i]
            if (loc.package != m.package or loc.file != m.file
                    or loc.line != m.line):
                s += COST_LOC_NONE
                d.append(("traceability", None, loc))
            else:
                p += COST_LOC_NONE
                d.append(("traceability", m, loc))
                del missed[i]
    for loc in bucket2:
        i = bisect(missed, loc)
        if i >= len(missed): # no match candidate
            s += COST_LOC_PKG
            d.append(("traceability", None, loc))
        else: # there is a match candidate
            m = missed[i]
            if loc.package != m.package or loc.file != m.file:
                s += COST_LOC_PKG
                d.append(("traceability", None, loc))
            else:
                p += COST_LOC_PKG
                d.append(("traceability", m, loc))
                del missed[i]
    for loc in bucket1:
        i = bisect(missed, loc)
        if i >= len(missed): # no match candidate
            s += COST_LOC_FILE
            d.append(("traceability", None, loc))
        else: # there is a match candidate
            m = missed[i]
            if loc.package != m.package:
                s += COST_LOC_FILE
                d.append(("traceability", None, loc))
            else:
                p += COST_LOC_FILE
                d.append(("traceability", m, loc))
                del missed[i]
    for loc in missed:
        d.append(("traceability", loc, None))
    assert p <= n
    return (n - p) + s


def location_buckets(locs):
    bucket1 = [] # one component
    bucket2 = [] # two components
    bucket3 = [] # three components
    bucket4 = [] # all components
    for loc in locs:
        if loc.package is None:
            continue
        if loc.file is None:
            bucket1.append(loc)
        elif loc.line is None:
            bucket2.append(loc)
        elif loc.column is None:
            bucket3.append(loc)
        else:
            bucket4.append(loc)
    return bucket1, bucket2, bucket3, bucket4


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
    if t1 == t2:
        return 0
    d.append(("traceability", t1, t2))
    if t1.package != t2.package:
        return COST_LOC_NONE
    if t1.file != t2.file:
        return COST_LOC_PKG
    assert t1.line != t2.line or t1.column != t2.column
    return COST_LOC_FILE


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

def diff_from_paths(paths, truth, model):
    diff = Diff([], [], [], [], [], [])
    for node_list, edge_list in paths:
        for u, v in node_list:
            assert not (u is None and v is None)
            if u is None:
                d = model.nodes[v]
                t = TYPES[d["nxtype"]]
                diff.spurious_nodes.append((t, v))
            elif v is None:
                d = truth.nodes[u]
                t = TYPES[d["nxtype"]]
                diff.missed_nodes.append((t, u))
            else:
                _, d = node_subst_cost_2(
                    truth.nodes[u], model.nodes[v], diff=True)
                if d:
                    t = TYPES[truth.nodes[u]["nxtype"]]
                    diff.partial_nodes.append((t, u, v, d))
        for a, b in edge_list:
            assert not (a is None and b is None)
            if a is None:
                d = model.edges[b]
                t = TYPES[d["nxtype"]]
                diff.spurious_edges.append((t, b[0], b[1]))
            elif b is None:
                d = truth.edges[a]
                t = TYPES[d["nxtype"]]
                diff.missed_edges.append((t, a[0], a[1]))
            else:
                e1 = truth.edges[a]
                e2 = model.edges[b]
                _, d = edge_subst_cost_2(e1, e2, diff=True)
                if d:
                    t = TYPES[e1["nxtype"]]
                    diff.partial_edges.append((t, a[0], a[1], b[0], b[1], d))
    return diff


###############################################################################
# Attribute Counting Functions
###############################################################################

def sizeof_graph(G):
    n = 0
    for u in G.nodes.values():
        n += sizeof_node(u)
    for a in G.edges.values():
        n += sizeof_edge(a)
    return n


def sizeof_node(u):
    nxtype = u["nxtype"]
    if nxtype == NODE:
        return node_size(u)
    elif nxtype == TOPIC:
        return topic_size(u)
    elif nxtype == SERVICE:
        return service_size(u)
    else:
        assert nxtype == PARAMETER
        return param_size(u)

def node_size(u):
    # rosname
    # node_type
    # args
    # conditions
    # traceability
    cn = conditions_size(u["conditions"])
    tn = traceability_size()
    return 3 + cn + tn

def topic_size(u):
    # rosname
    # msg_type
    # conditions
    # traceability
    cn = conditions_size(u["conditions"])
    tn = traceability_list_size(u["traceability"])
    return 2 + cn + tn

def service_size(u):
    # rosname
    # srv_type
    # conditions
    # traceability
    cn = conditions_size(u["conditions"])
    tn = traceability_list_size(u["traceability"])
    return 2 + cn + tn

def param_size(u):
    # rosname
    # default_value
    # conditions
    # traceability
    cn = conditions_size(u["conditions"])
    tn = traceability_list_size(u["traceability"])
    return 2 + cn + tn


def sizeof_edge(a):
    nxtype = a["nxtype"]
    if nxtype == PUBLISHER:
        return publisher_size(a)
    elif nxtype == SUBSCRIBER:
        return subscriber_size(a)
    elif nxtype == SERVER:
        return server_size(a)
    elif nxtype == CLIENT:
        return client_size(a)
    elif nxtype == GET:
        return get_param_size(a)
    else:
        assert nxtype == SET
        return set_param_size(a)

def publisher_size(a):
    # rosname
    # msg_type
    # queue_size
    # conditions
    # traceability
    cn = conditions_size(a["conditions"])
    tn = traceability_size()
    return 3 + cn + tn

def subscriber_size(a):
    return publisher_size(a)

def server_size(a):
    # rosname
    # srv_type
    # conditions
    # traceability
    cn = conditions_size(a["conditions"])
    tn = traceability_size()
    return 2 + cn + tn

def client_size(a):
    return server_size(a)

def get_param_size(a):
    # rosname
    # param_type
    # conditions
    # traceability
    cn = conditions_size(a["conditions"])
    tn = traceability_size()
    return 2 + cn + tn

def set_param_size(a):
    return get_param_size(a)

def conditions_size(cfg):
    n = 0
    queue = [cfg]
    while queue:
        new_queue = []
        for g in queue:
            for guard, child in g.items():
                n += 1
                new_queue.append(child)
        queue = new_queue
    return n

def traceability_size():
    return COST_LOC_NONE

def traceability_list_size(locs):
    return traceability_size() * len(locs)


###############################################################################
# Helper Classes
###############################################################################

class NullList(object):
    __slots__ = ()

    def append(self, item):
        pass

    def extend(self, items):
        pass
