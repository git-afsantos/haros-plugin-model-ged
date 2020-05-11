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

from networkx import graph_edit_distance, optimal_edit_paths

from .haros2nx import (
    NODE, TOPIC, SERVICE, PARAMETER,
    PUBLISHER, SUBSCRIBER, SERVER, CLIENT, GET, SET
)

###############################################################################
# Constants
###############################################################################

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
        nsc = node_subst_cost_2
        esc = edge_subst_cost_2
    else:
        nsc = node_subst_cost_0
        esc = edge_subst_cost_0
    return graph_edit_distance(G1, G2,
        node_subst_cost=nsc,
        node_del_cost=None, # defaults to 1
        node_ins_cost=None, # defaults to 1
        edge_subst_cost=esc,
        edge_del_cost=None, # defaults to 1
        edge_ins_cost=None) # defaults to 1

def calc_edit_paths(G1, G2, ext=False):
    if ext:
        nsc = node_subst_cost_2
        esc = edge_subst_cost_2
    else:
        nsc = node_subst_cost_0
        esc = edge_subst_cost_0
    return optimal_edit_paths(G1, G2,
        node_subst_cost=nsc,
        node_del_cost=None, # defaults to 1
        node_ins_cost=None, # defaults to 1
        edge_subst_cost=esc,
        edge_del_cost=None, # defaults to 1
        edge_ins_cost=None) # defaults to 1


###############################################################################
# GED Node Cost Functions
###############################################################################

# node_subst_cost(G1.nodes[n1], G2.nodes[n2])
# node_del_cost(G1.nodes[n1])
# node_ins_cost(G2.nodes[n2])

def node_subst_cost_0(u, v):
    if u["nxtype"] != v["nxtype"]:
        return 2.0
    cost = 0.0
    udata = u["rosname"]
    vdata = v["rosname"]
    if "?" in vdata:
        cost = 0.5
    elif udata != vdata:
        cost = 1.0
    return cost

def node_subst_cost_2(u, v, diff=False):
    # u: graph node from ground truth
    # v: graph node from extracted model
    # should be the dict attributes for each node
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    nxtype = u["nxtype"]
    if nxtype != v["nxtype"]:
        return 2.0
    d = []
    total = float(len(v) - 1) # ignore metadata
    score = total # start with everything right and apply penalties
    score -= cmp_resource(u, v, d)
    if nxtype == NODE:
        score -= cmp_node_ext(u, v, d)
    elif nxtype == TOPIC:
        score -= cmp_topic_ext(u, v, d)
    elif nxtype == SERVICE:
        score -= cmp_service_ext(u, v, d)
    else:
        assert nxtype == PARAMETER
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
    penalty += cmp_conditions(u["conditions"], v["conditions"], d)
    penalty += cmp_traceability(u["traceability"], v["traceability"], d)
    return penalty

def cmp_topic_ext(u, v, d):
    penalty = 0.0
    penalty += cmp_conditions(u["conditions"], v["conditions"], d)
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty

def cmp_service_ext(u, v, d):
    penalty = 0.0
    penalty += cmp_conditions(u["conditions"], v["conditions"], d)
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty

def cmp_param_ext(u, v, d):
    penalty = 0.0
    udata = u["default_value"]
    vdata = v["default_value"]
    if udata != vdata:
        penalty += 1.0
        d.append(("default_value", udata, vdata))
    penalty += cmp_conditions(u["conditions"], v["conditions"], d)
    penalty += cmp_traceability_list(u["traceability"], v["traceability"], d)
    return penalty


###############################################################################
# GED Edge Cost Functions
###############################################################################

# edge_subst_cost(G1[u1][v1], G2[u2][v2])
# edge_del_cost(G1[u1][v1])
# edge_ins_cost(G2[u2][v2])

def edge_subst_cost_0(a, b):
    if a["nxtype"] != b["nxtype"]:
        return 2.0
    return 0.0

def edge_subst_cost_2(a, b, diff=False):
    # receives the edge attribute dictionaries as inputs
    # a: graph edge from ground truth
    # b: graph edge from extracted model
    # final result is a cost in [0.0, 1.0]
    #   where 0.0 is perfect and 1.0 is completely wrong
    nxtype = a["nxtype"]
    if nxtype != b["nxtype"]:
        return 2.0
    d = []
    total = float(len(b) - 1) # ignore metadata
    score = total # start with everything right and apply penalties
    score -= cmp_link(a, b, d)
    if nxtype == PUBLISHER or nxtype == SUBSCRIBER:
        score -= cmp_pubsub_ext(a, b, d)
    elif nxtype == SERVER or nxtype == CLIENT:
        score -= cmp_srvcli_ext(a, b, d)
    else:
        assert nxtype == GET or nxtype == SET
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
    penalty += cmp_conditions(a["conditions"], b["conditions"], d)
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

def cmp_conditions(cfg1, cfg2, d):
    # list of lists of conditions - a path
    if not cfg1 and cfg2:
        return 1.0
    if cfg1 and not cfg2:
        return 1.0
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
    penalty = 1.0 - f1(n, p, s)
    assert penalty >= 0.0 and penalty <= 1.0
    return penalty


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
        p = loc.package
        f = loc.file
        l = loc.line
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
    if t2 is None:
        d.append(("traceability", t1, t2))
        return 1.0
    if t1.package != t2.package:
        d.append(("traceability", t1, t2))
        return 1.0
    if t1.file != t2.file:
        d.append(("traceability", t1, t2))
        return 0.5
    if t1.line != t2.line:
        d.append(("traceability", t1, t2))
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
