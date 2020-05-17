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
from timeit import default_timer as timer

from .graph_matching import (
    matching_by_name_type_loc, matching_by_loc_name_type, rosname_match
)

###############################################################################
# Graph Difference Calculation
###############################################################################

Diff = namedtuple("Diff",
    ("resource_type", "rosname", "attribute", "p_value", "g_value"))

MetricsTuple = namedtuple("MetricsTuple",
    ("cor", "inc", "par", "mis", "spu", "pre", "rec", "f1"))

Report = namedtuple("Report", ("metrics", "diffs"))

ResourceReport = namedtuple("ResourceReport",
    ("node", "parameter", "publisher", "subscriber",
     "client", "server", "setter", "getter"))

# {'*': combined metrics, 'attr': combined attr metrics}
AggregateReport = namedtuple("AggregateReport",
    ("overall", "launch", "source", "topics", "services", "params"))

PerformanceReport = namedtuple("PerformanceReport",
    ("aggregate", "resource", "match_time", "report_time"))


class GraphDiffCalculator(object):
    def __init__(self):
        self.node_perf = NodePerformanceEvaluator()
        self.param_perf = ParamPerformanceEvaluator()
        self.pub_perf = PubPerformanceEvaluator()
        self.sub_perf = SubPerformanceEvaluator()
        self.cli_perf = ClientPerformanceEvaluator()
        self.srv_perf = ServerPerformanceEvaluator()
        self.setter_perf = SetterPerformanceEvaluator()
        self.getter_perf = GetterPerformanceEvaluator()

    def report(self, config, truth):
        # ---- SETUP PHASE ----------------------------------------------------
        start_time = timer()
        match_data = matching_by_name_type_loc(config, truth)
        end_time = timer()
        match_time = end_time - start_time
        # ---- REPORT PHASE ---------------------------------------------------
        start_time = timer()
        res = self._resource_reports(match_data)
        agg = self._aggregate_reports()
        end_time = timer()
        report_time = end_time - start_time
        # ---- RETURN PHASE ---------------------------------------------------
        return PerformanceReport(agg, res, match_time, report_time)

    def _resource_reports(self, match_data):
        return ResourceReport(
            self.node_perf.report(match_data.nodes),
            self.param_perf.report(match_data.parameters),
            self.pub_perf.report(match_data.publishers),
            self.sub_perf.report(match_data.subscribers),
            self.cli_perf.report(match_data.clients),
            self.srv_perf.report(match_data.servers),
            self.setter_perf.report(match_data.setters),
            self.getter_perf.report(match_data.getters))

    def _aggregate_reports(self):
        overall_metrics = self._combined_metrics((
            self.node_perf, self.param_perf,
            self.pub_perf, self.sub_perf, self.cli_perf,
            self.srv_perf, self.setter_perf, self.getter_perf),
            all_attrs=False)
        launch_metrics = self._combined_metrics((
            self.node_perf, self.param_perf),
            all_attrs=False)
        source_metrics = self._combined_metrics((
            self.pub_perf, self.sub_perf, self.cli_perf, self.srv_perf,
            self.setter_perf, self.getter_perf),
            all_attrs=False)
        topic_metrics = self._combined_metrics((
            self.pub_perf, self.sub_perf))
        service_metrics = self._combined_metrics((
            self.cli_perf, self.srv_perf))
        param_metrics = self._combined_metrics((
            self.setter_perf, self.getter_perf))
        return AggregateReport(overall_metrics, launch_metrics, source_metrics,
            topic_metrics, service_metrics, param_metrics)

    def _combined_metrics(self, perfs, all_attrs=True):
        if all_attrs:
            keys = perfs[0].metrics.keys()
        else:
            keys = PerformanceEvaluator.main_attrs
        r = {}
        for key in keys:
            m = Metrics()
            for perf in perfs:
                m.add(perf.get_metrics(key))
            r[key] = m.as_tuple()
        m = perfs[0].combined_metrics()
        for i in range(1, len(perfs)):
            m.add(perfs[i].combined_metrics())
        r["*"] = m.as_tuple()
        return r


def calc_performance(config, truth):
    g = GraphDiffCalculator()
    return g.report(config, truth)


###############################################################################
# Comparison Functions
###############################################################################

class Metrics(object):
    __slots__ = ("cor", "inc", "par", "mis", "spu")

    def __init__(self):
        self.cor = 0
        self.inc = 0
        self.par = 0
        self.mis = 0
        self.spu = 0

    @property
    def n(self):
        return self.cor + self.inc + self.par + self.mis + self.spu

    @property
    def pos(self):
        return self.cor + self.inc + self.par + self.mis

    @property
    def act(self):
        return self.cor + self.inc + self.par + self.spu

    @property
    def precision(self):
        act = self.act
        if act == 0.0:
            return 1.0
        return (self.cor + 0.5 * self.par) / act

    @property
    def recall(self):
        pos = self.pos
        if pos == 0.0:
            return 1.0
        return (self.cor + 0.5 * self.par) / pos

    @property
    def f1(self):
        p = self.precision
        r = self.recall
        if (p + r) == 0.0:
            return 0.0
        return 2 * p * r / (p + r)

    def as_tuple(self):
        return MetricsTuple(self.cor, self.inc, self.par, self.mis, self.spu,
            self.precision, self.recall, self.f1)

    def add(self, metrics):
        self.cor += metrics.cor
        self.inc += metrics.inc
        self.par += metrics.par
        self.mis += metrics.mis
        self.spu += metrics.spu
        return self


class PerformanceEvaluator(object):
    resource_type = "Resource"
    __slots__ = ("metrics", "diffs")
    main_attrs = ("rosname", "rostype", "traceability", "conditions")
    snd_attrs = ()

    def report(self, M):
        self._reset()
        self._count_missing(M)
        self._count_spurious(M)
        for u, v in M.matches:
            self._count_rosname(u, v)
            self._count_rostype(u, v)
            self._count_traceability(u, v)
            self._count_conditions(u, v)
            self._count_secondary_attrs(u, v)
        metrics = {key: m.as_tuple() for key, m in self.metrics.items()}
        metrics["*"] = self.combined_metrics().as_tuple()
        return Report(metrics, self.diffs)

    def get_metrics(self, attr):
        m = self.metrics.get(attr)
        if m is None:
            return Metrics()
        return m

    def combined_metrics(self):
        metrics = Metrics()
        for m in self.metrics.values():
            metrics.add(m)
        return m

    def _reset(self):
        self.diffs = []
        self.metrics = {}
        for attr in self.main_attrs:
            self.metrics[attr] = Metrics()
        for attr in self.snd_attrs:
            self.metrics[attr] = Metrics()

    def _count_missing(self, M):
        if M.missing:
            for m in self.metrics.values():
                m.mis += len(M.missing)
            for v in M.missing:
                self._diff(v.rosname, "*", None, v)

    def _count_spurious(self, M):
        if M.spurious:
            for m in self.metrics.values():
                m.spu += len(M.spurious)
            for u in M.spurious:
                self._diff(u.rosname, "*", u, None)

    def _count_rosname(self, u, v):
        m = self.metrics["rosname"]
        if u.rosname == v.rosname:
            m.cor += 1
        else:
            if "?" in u.rosname and rosname_match(u.rosname, v.rosname):
                m.par += 1
            else:
                m.inc += 1
            self._diff(v.rosname, "ROS name", u.rosname, v.rosname)

    def _count_rostype(self, u, v):
        m = self.metrics["rostype"]
        if u.rostype == v.rostype:
            m.cor += 1
        else:
            m.inc += 1
            self._diff(v.rosname, "ROS type", u.rostype, v.rostype)

    def _count_traceability(self, u, v):
        m = self.metrics["traceability"]
        p = u.traceability
        g = v.traceability
        if p == g:
            m.cor += 1
        else:
            m.inc += 1
            if p.package != g.package:
                self._diff(v.rosname, "traceability:package",
                    p.package, g.package)
            elif p.file != g.file:
                self._diff(v.rosname, "traceability:file", p.file, g.file)
            elif p.line != g.line:
                self._diff(v.rosname, "traceability:line", p.line, g.line)
            elif p.column != g.column:
                self._diff(v.rosname, "traceability:column",
                    p.column, g.column)

    def _count_conditions(self, u, v):
        m = self.metrics["conditions"]
        cfg1 = u.conditions
        cfg2 = v.conditions
        if not cfg1 and cfg2:
            m.inc += 1
        elif cfg1 and not cfg2:
            m.inc += 1
        else:
            n = p = s = 0
            queue = [(cfg1, cfg2)]
            while queue:
                new_queue = []
                for c1, c2 in queue:
                    for g, child1 in c1.items():
                        n += 1
                        child2 = c2.get(g)
                        if child2 is None:
                            self._diff(v.rosname, "condition", g, None)
                        else:
                            p += 1
                            new_queue.append((child1, child2))
                    for g, child2 in c2.items():
                        child1 = c1.get(g)
                        if child1 is None:
                            s += 1
                            self._diff(v.rosname, "condition", None, g)
                queue = new_queue
            if s > 0:
                if p == n:
                    m.spu += 1
                elif p > 0:
                    m.par += 1
                else:
                    m.inc += 1
            else:
                if p == n:
                    m.cor += 1
                elif p > 0:
                    m.par += 1
                else:
                    m.mis += 1

    def _count_secondary_attrs(self, u, v):
        for attr in self.snd_attrs:
            f = "_count_" + attr
            if hasattr(self, f):
                getattr(self, f)(u, v)
            else:
                self._count_simple_attr(u, v, attr)

    def _count_simple_attr(self, u, v, attr):
        p = getattr(u, attr)
        g = getattr(v, attr)
        if p == g:
            self.metrics[attr].cor += 1
        else:
            self.metrics[attr].inc += 1
            self._diff(v.rosname, attr.replace("_", " "), p, g)

    def _diff(self, rosname, attr, p, g):
        self.diffs.append(Diff(self.resource_type, rosname, attr, p, g))


class NodePerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("args",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Node"

class ParamPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("value",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Parameter"

class PubPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name", "queue_size", "latched",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Topic Publisher"

class SubPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name", "queue_size",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Topic Subscriber"

class ClientPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Service Client"

class ServerPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name",)
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Service Server"

class SetterPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name", "value")
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Parameter Setter"

class GetterPerformanceEvaluator(PerformanceEvaluator):
    snd_attrs = ("original_name", "value")
    __slots__ = PerformanceEvaluator.__slots__ + snd_attrs
    resource_type = "Parameter Getter"
