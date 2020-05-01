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

from networkx import MultiDiGraph


###############################################################################
# Constants
###############################################################################

NODE = 1
TOPIC = 2
SERVICE = 3
PARAMETER = 4

PUBLISHER = 11
SUBSCRIBER = 12
SERVER = 13
CLIENT = 14
GET = 15
SET = 16


###############################################################################
# Helper Classes
###############################################################################

Guard = namedtuple("Guard",
    ("statement", "condition", "package", "file", "line", "column"))

Location = namedtuple("Location", ("package", "file", "line", "column"))


###############################################################################
# HAROS to NetworkX Conversion
###############################################################################

def config_to_nx(config):
    objs = {}
    G = MultiDiGraph(ids={})
    haros_nodes_to_nx(config.nodes.enabled, G)
    haros_topics_to_nx(config.topics.enabled, G)
    haros_services_to_nx(config.services.enabled, G)
    haros_params_to_nx(config.parameters.enabled, G)
    haros_links_to_nx(config.nodes.enabled, G)
    return G


###############################################################################
# Graph Node Attributes
###############################################################################

def haros_nodes_to_nx(nodes, G):
    for node in nodes:
        rosname = node.rosname.full
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

def haros_conditions_to_nx(conditions):
    cfg = {}
    for condition in conditions:
        loc = haros_location_to_nx(condition.location)
        g = Guard("if", condition.condition,
            loc.package, loc.file, loc.line, loc.column)
        cfg[g] = {}
    return cfg

def haros_location_to_nx(loc):
    if loc is None or loc.package is None:
        return Location(None, None, None, None)
    if loc.file is None:
        return Location(loc.package.name, None, None, None)
    return Location(loc.package.name, loc.file.full_name, loc.line, loc.column)


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
            traceability=yaml_to_location(param["traceability"]))

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
        attrs["conditions"] = {}
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
        attrs["conditions"] = {}
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
        attrs["conditions"] = {}
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
    return Location(traceability["package"], traceability["file"],
        traceability["line"], traceability["column"])
