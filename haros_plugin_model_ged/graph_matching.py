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

from collections import namedtuple

import networkx as nx
from networkx.algorithms import bipartite


###############################################################################
# Helper Classes
###############################################################################

Graph = namedtuple("Graph",
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

def matching_by_name_type(config, truth):

def matching_by_name_type_loc(config, truth):

def matching_by_loc(config, truth):

def calc_matching(config, truth, cost_node=None, cost_param=None,
        cost_pub=None, cost_sub=None, cost_cli=None, cost_srv=None,
        cost_set=None, cost_get=None):
    P = config2graph(config)
    G = truth2graph(truth)
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

def cost_node(u, v):
    cost = 0
    return cost

def cost_param(u, v):
    cost = 0
    return cost

def cost_pub(u, v):
    cost = 0
    return cost

def cost_sub(u, v):
    cost = 0
    return cost

def cost_cli(u, v):
    cost = 0
    return cost

def cost_srv(u, v):
    cost = 0
    return cost

def cost_set(u, v):
    cost = 0
    return cost

def cost_get(u, v):
    cost = 0
    return cost


###############################################################################
# HAROS Conversion Functions
###############################################################################

def convert_haros_node(i, node):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return NodeAttrs(i, node.id, rostype, traceability, args, conditions)

def convert_haros_param(i, param):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return ParamAttrs(i, param.id, rostype, traceability, value, conditions)

def convert_haros_pub(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return PubAttrs(i, link.node.id, link.topic.id, link.type, traceability,
        link.rosname.full, link.queue_size, False, conditions)

def convert_haros_sub(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return SubAttrs(i, link.node.id, link.topic.id, link.type, traceability,
        link.rosname.full, link.queue_size, conditions)

def convert_haros_cli(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return CliAttrs(i, link.node.id, link.service.id, link.type, traceability,
        link.rosname.full, conditions)

def convert_haros_srv(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return SrvAttrs(i, link.node.id, link.service.id, link.type, traceability,
        link.rosname.full, conditions)

def convert_haros_setter(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
    return SetAttrs(i, link.node.id, link.parameter.id, link.type, traceability,
        link.rosname.full, None, conditions)

def convert_haros_getter(i, link):
    traceability = convert_haros_location()
    conditions = convert_haros_conditions()
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
    return NodeAttrs(i, rosname, rostype, traceability, args, conditions)

def convert_truth_param(i, rosname, data):
    return ParamAttrs(i, rosname, rostype, traceability, value, conditions)

def convert_truth_pub(i, link):
    return PubAttrs(i, node, rosname, rostype, traceability, original_name,
     queue_size, latched, conditions)

def convert_truth_sub(i, link):
    return SubAttrs(i, node, rosname, rostype, traceability, original_name,
     queue_size, conditions)

def convert_truth_cli(i, link):
    return CliAttrs(i, node, rosname, rostype, traceability, original_name,
     conditions)

def convert_truth_srv(i, link):
    return SrvAttrs(i, node, rosname, rostype, traceability, original_name,
     conditions)

def convert_truth_setter(i, link):
    return SetAttrs(i, node, rosname, rostype, traceability, original_name,
     value, conditions)

def convert_truth_getter(i, link):
    return GetAttrs(i, node, rosname, rostype, traceability, original_name,
     value, conditions)


def convert_truth_traceability(traceability):

def convert_truth_conditions(conditions):


###############################################################################
# HAROS Conversion Functions
###############################################################################

def config_to_graph(config):
    ids = {}
    G = Graph({}, {}, {}, {}, {}, {}, {}, {}, {}, {})
    haros_nodes_to_nx(config.nodes.enabled, G, ids)
    haros_topics_to_nx(config.topics.enabled, G)
    haros_services_to_nx(config.services.enabled, G)
    haros_params_to_nx(config.parameters.enabled, G)
    haros_links_to_nx(config.nodes.enabled, G)
    return G


class HarosGraph(object):
    __slots__ = ('nodes', 'u_nodes', 'topics', 'u_topics', 'services',
        'u_services', 'params', 'u_params', 'pubs', 'subs', )

    def __init__(self, config):
        self.nodes = {}
        self.u_nodes = []
        self.topics = {}
        self.u_topics = []
        self.services = {}
        self.u_services = []
        self.params = {}
        self.u_params = []

    def _build_nodes(self, config):
        self.nodes = {}
        self.u_nodes = []
        for node in config.nodes.enabled:
            if node.unresolved:
                self.u_nodes.append(node)
            else:
                self.nodes[node.rosname.full] = node

    def _cmp_nodes(self, truth):
        missing = dict(truth['launch'].get('nodes', {}))
        n = len(missing)
        for rosname, node in self.nodes.items():
            if rosname in missing:
                p += 1
                # delta
                del missing[rosname]
            else:
                s += 1
        for rosname, data in missing.items():
            best = None
            score = 0
            for node in self.u_nodes:
                x = 0
                if node.node.node_name == data['node_type']:
                    x += 1
                    if traceability match:
                    


###############################################################################
# Graph Node Attributes
###############################################################################

def haros_nodes_to_nx(nodes, G, ids):
    i = 0
    for node in nodes:
        rosname = node.rosname.full
        if rosname.is_unresolved:
            i += 1
            rosname = rosname.replace("?", "(?{})".format(i))
        uid = "[N{}]{}".format(len(G), rosname)
        G.graph["ids"][node] = uid
        G.add_node(uid, nxtype=NODE, rosname=rosname,
            node_type=node.node.node_name, args=node.argv,
            conditions=haros_conditions_to_nx(node.conditions),
            traceability=haros_location_to_nx(node.traceability()[0]))

def haros_topics_to_nx(topics, G):
    for topic in topics:
        rosname = topic.rosname.full
        uid = "[T{}]{}".format(len(G), rosname)
        traceability = list(set(haros_location_to_nx(loc)
                                for loc in topic.traceability()))
        G.graph["ids"][topic] = uid
        G.add_node(uid, nxtype=TOPIC, rosname=rosname, msg_type=topic.type,
            conditions=haros_conditions_to_nx(topic.conditions),
            traceability=traceability)

def haros_services_to_nx(services, G):
    for srv in services:
        rosname = srv.rosname.full
        uid = "[S{}]{}".format(len(G), rosname)
        traceability = list(set(haros_location_to_nx(loc)
                                for loc in srv.traceability()))
        G.graph["ids"][srv] = uid
        G.add_node(uid, nxtype=SERVICE, rosname=rosname, srv_type=srv.type,
            conditions=haros_conditions_to_nx(srv.conditions),
            traceability=traceability)

def haros_params_to_nx(parameters, G):
    for param in parameters:
        rosname = param.rosname.full
        uid = "[P{}]{}".format(len(G), rosname)
        traceability = list(set(haros_location_to_nx(loc)
                                for loc in param.traceability()))
        G.graph["ids"][param] = uid
        G.add_node(uid, nxtype=PARAMETER, rosname=rosname,
            default_value=param.value,
            conditions=haros_conditions_to_nx(param.conditions),
            traceability=traceability)


###############################################################################
# Graph Edge Attributes
###############################################################################

def haros_links_to_nx(nodes, G):
    for node in nodes:
        haros_publishers_to_nx(node.publishers, G)
        haros_subscribers_to_nx(node.subscribers, G)
        haros_servers_to_nx(node.servers, G)
        haros_clients_to_nx(node.clients, G)
        haros_get_params_to_nx(node.reads, G)
        haros_set_params_to_nx(node.writes, G)

def haros_publishers_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.node]
        t = G.graph["ids"][link.topic]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=PUBLISHER, rosname=link.rosname.full,
            msg_type=link.type, queue_size=link.queue_size,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))

def haros_subscribers_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.topic]
        t = G.graph["ids"][link.node]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SUBSCRIBER, rosname=link.rosname.full,
            msg_type=link.type, queue_size=link.queue_size,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))

def haros_servers_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.service]
        t = G.graph["ids"][link.node]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SERVER, rosname=link.rosname.full,
            srv_type=link.type,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))

def haros_clients_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.node]
        t = G.graph["ids"][link.service]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=CLIENT, rosname=link.rosname.full,
            srv_type=link.type,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))

def haros_get_params_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.parameter]
        t = G.graph["ids"][link.node]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=GET, rosname=link.rosname.full,
            param_type=link.type,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))

def haros_set_params_to_nx(links, G):
    for link in links:
        s = G.graph["ids"][link.node]
        t = G.graph["ids"][link.parameter]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SET, rosname=link.rosname.full,
            param_type=link.type,
            conditions=haros_conditions_to_nx(link.conditions),
            traceability=haros_location_to_nx(link.source_location))


###############################################################################
# Nested Attributes
###############################################################################




###############################################################################
# Ground Truth to NetworkX Conversion
###############################################################################

def truth_to_nx(truth):
    G = MultiDiGraph()
    launch = truth.get("launch")
    if launch:
        truth_launch_to_nx(launch, G)
        links = truth.get("links")
        if links:
            truth_msg_links_to_nx(links, G)
            truth_srv_links_to_nx(links, G)
            truth_param_links_to_nx(links, G)
    not_nodes = (TOPIC, SERVICE, PARAMETER)
    for u in G.nodes.values():
        nxtype = u["nxtype"]
        if nxtype in not_nodes:
            if True in u["conditions"]:
                u["conditions"] = {}
    return G


###############################################################################
# Graph Node Attributes
###############################################################################

def truth_launch_to_nx(launch, G):
    for rosname, node in launch.get("nodes", {}).items():
        uid = "[N]" + rosname
        G.add_node(uid, nxtype=NODE, rosname=rosname,
            node_type=node["node_type"], args=node.get("args", []),
            conditions=cfg_from_list(node.get("conditions", ())),
            traceability=yaml_to_location(node["traceability"]))
    for rosname, param in launch.get("parameters", {}).items():
        uid = "[P]" + rosname
        G.add_node(uid, nxtype=PARAMETER, rosname=rosname,
            default_value=param.get("default_value"),
            conditions=cfg_from_list(param.get("conditions", ())),
            traceability=[yaml_to_location(param["traceability"])])

def topic_from_link(link, G):
    rosname = link["topic"]
    uid = "[T]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        G.add_node(uid, nxtype=TOPIC, rosname=rosname,
            msg_type=link["msg_type"],
            conditions={}, traceability=[])
        attrs = G.nodes[uid]
    cfg = cfg_from_list(link.get("conditions", ()))
    if cfg:
        attrs["conditions"].update(cfg)
    else:
        attrs["conditions"] = {True: None}
    attrs["traceability"].append(yaml_to_location(link["traceability"]))

def service_from_link(link, G):
    rosname = link["service"]
    uid = "[S]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        G.add_node(uid, nxtype=SERVICE, rosname=rosname,
            srv_type=link["srv_type"],
            conditions={}, traceability=[])
        attrs = G.nodes[uid]
    cfg = cfg_from_list(link.get("conditions", ()))
    if cfg:
        attrs["conditions"].update(cfg)
    else:
        attrs["conditions"] = {True: None}
    attrs["traceability"].append(yaml_to_location(link["traceability"]))

def param_from_link(link, G):
    rosname = link["parameter"]
    uid = "[P]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        G.add_node(uid, nxtype=PARAMETER, rosname=rosname, default_value=None,
            conditions={}, traceability=[])
        attrs = G.nodes[uid]
    cfg = cfg_from_list(link.get("conditions", ()))
    if cfg:
        attrs["conditions"].update(cfg)
    else:
        attrs["conditions"] = {True: None}
    attrs["traceability"].append(yaml_to_location(link["traceability"]))


###############################################################################
# Graph Edge Attributes
###############################################################################

def truth_msg_links_to_nx(links, G):
    for link in links.get("publishers", ()):
        topic = link["topic"]
        topic_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[T]" + topic
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=PUBLISHER,
            rosname=link.get("rosname", topic),
            msg_type=link["msg_type"], queue_size=link["queue_size"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))
    for link in links.get("subscribers", ()):
        topic = link["topic"]
        topic_from_link(link, G)
        s = "[T]" + topic
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SUBSCRIBER,
            rosname=link.get("rosname", topic),
            msg_type=link["msg_type"], queue_size=link["queue_size"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))

def truth_srv_links_to_nx(links, G):
    for link in links.get("clients", ()):
        service = link["service"]
        service_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[S]" + service
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=CLIENT,
            rosname=link.get("rosname", service),
            srv_type=link["srv_type"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))
    for link in links.get("servers", ()):
        service = link["service"]
        service_from_link(link, G)
        s = "[S]" + service
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SERVER,
            rosname=link.get("rosname", service),
            srv_type=link["srv_type"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))

def truth_param_links_to_nx(links, G):
    for link in links.get("sets", ()):
        param = link["parameter"]
        param_from_link(link, G)
        s = "[N]" + link["node"]
        t = "[P]" + param
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=SET,
            rosname=link.get("rosname", param),
            param_type=link["param_type"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))
    for link in links.get("gets", ()):
        param = link["parameter"]
        param_from_link(link, G)
        s = "[P]" + param
        t = "[N]" + link["node"]
        uid = "{} -> {}".format(s, t)
        G.add_edge(s, t, key=uid, nxtype=GET,
            rosname=link.get("rosname", param),
            param_type=link["param_type"],
            conditions=cfg_from_list(link.get("conditions", ())),
            traceability=yaml_to_location(link["traceability"]))


def cfg_from_list(paths):
    cfg = {}
    for path in paths:
        r = cfg
        for c in path:
            g = Guard(c["statement"], c["condition"],
                      c["package"], c["file"], c["line"], c["column"])
            s = r.get(g)
            if s is None:
                s = {}
                r[g] = s
            r = s
    return cfg

def yaml_to_location(traceability):
    if traceability is None:
        return Location(None, None, None, None)
    return Location(traceability["package"], traceability["file"],
        traceability["line"], traceability["column"])
