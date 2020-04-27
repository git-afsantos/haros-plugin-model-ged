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

from .common import *

###############################################################################
# Helper Classes
###############################################################################

Guard = namedtuple("Guard",
    ("statement", "condition", "package", "file", "line"))


###############################################################################
# HAROS to NetworkX Conversion
###############################################################################

def config_to_nx(config, ext=False):
    objs = {}
    G = MultiDiGraph()
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
# Graph Node Attributes
###############################################################################

def node_attrs(node, ext=False):
    attrs = {
        "resource_type": NODE,
        "rosname": node.rosname.full
    }
    if ext:
        attrs.update({
            "node_type": node.node.node_name,
            "args": node.argv,
            "conditions": condition_attrs(node.conditions),
            "traceability": location_attrs(node.traceability()[0])
        })
    return attrs

def topic_attrs(topic, ext=False):
    attrs = {
        "resource_type": TOPIC,
        "rosname": topic.rosname.full
    }
    if ext:
        attrs.update({
            "conditions": condition_attrs(topic.conditions),
            "traceability": [
                location_attrs(loc) for loc in topic.traceability()]
        })
    return attrs

def service_attrs(service, ext=False):
    attrs = {
        "resource_type": SERVICE,
        "rosname": service.rosname.full
    }
    if ext:
        attrs.update({
            "conditions": condition_attrs(service.conditions),
            "traceability": [
                location_attrs(loc) for loc in service.traceability()]
        })
    return attrs

def param_attrs(param, ext=False):
    attrs = {
        "resource_type": PARAMETER,
        "rosname": param.rosname.full
    }
    if ext:
        attrs.update({
            "default_value": param.value,
            "conditions": condition_attrs(param.conditions),
            "traceability": [
                location_attrs(loc) for loc in param.traceability()]
        })
    return attrs


def condition_attrs(conditions):
    cfg = {}
    for condition in conditions:
        loc = location_attrs(condition.location)
        g = Guard("if", condition.condition,
            loc["package"], loc["file"], loc["line"])
        cfg[g] = {}
    return cfg

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
            "conditions": condition_attrs(link.conditions),
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
            "conditions": condition_attrs(link.conditions),
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
            "conditions": condition_attrs(link.conditions),
            "traceability": location_attrs(link.source_location),
            "param_type": link.type
        })
    return attrs


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

def truth_launch_to_nx(launch, G):
    for node in launch.get("nodes", ()):
        attrs = dict(node)
        uid = "[N]" + attrs["rosname"]
        attrs["resource_type"] = NODE
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
        G.add_node(uid, **attrs)
    for param in launch.get("parameters", ()):
        attrs = dict(param)
        uid = "[P]" + attrs["rosname"]
        attrs["resource_type"] = PARAMETER
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
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
        attrs["conditions"] = cfg_from_list(attrs["conditions"])
        G.add_edge(s, t, key=uid, **attrs)


def topic_from_link(link, G):
    rosname = link["topic"]
    uid = "[T]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        attrs = {
            "resource_type": TOPIC,
            "rosname": rosname,
            "conditions": {},
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditions"].update(cfg_from_list(link["conditions"]))
    attrs["traceability"].append(link["traceability"])

def service_from_link(link, G):
    rosname = link["service"]
    uid = "[S]" + rosname
    attrs = G.nodes.get(uid)
    if attrs is None:
        attrs = {
            "resource_type": SERVICE,
            "rosname": rosname,
            "conditions": {},
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditions"].update(cfg_from_list(link["conditions"]))
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
            "conditions": {},
            "traceability": []
        }
        G.add_node(uid, **attrs)
        attrs = G.nodes[uid]
    attrs["conditions"].update(cfg_from_list(link["conditions"]))
    attrs["traceability"].append(link["traceability"])


def cfg_from_list(paths):
    cfg = {}
    for path in paths:
        r = cfg
        for c in path:
            g = Guard(c["statement"], c["condition"],
                      c["package"], c["file"], c["line"])
            s = r.get(g)
            if s is None:
                s = {}
                r[g] = s
            r = s
    return cfg