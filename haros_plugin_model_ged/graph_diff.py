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

Report = namedtuple("Report", ("lv1", "lv2", "lv3", "diffs"))

MultiReport = namedtuple("MultiReport",
    ("launch", "source", "node", "parameter", "publisher",
     "subscriber", "client", "server", "setter", "getter"))

PerformanceReport = namedtuple("PerformanceReport",
    ("overall", "by", "match_time", "report_time"))


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
        node_report = self.node_perf.report(match_data.nodes)
        param_report = self.param_perf.report(match_data.parameters)
        pub_report = self.pub_perf.report(match_data.publishers)
        sub_report = self.sub_perf.report(match_data.subscribers)
        cli_report = self.cli_perf.report(match_data.clients)
        srv_report = self.srv_perf.report(match_data.servers)
        setter_report = self.setter_perf.report(match_data.setters)
        getter_report = self.getter_perf.report(match_data.getters)
        end_time = timer()
        report_time = end_time - start_time
        # ---- RETURN PHASE ---------------------------------------------------
        return PerformanceReport(self._overall_report(),
            MultiReport(self._launch_report(), self._source_report(),
                        node_report, param_report, pub_report, sub_report,
                        cli_report, srv_report, setter_report, getter_report),
            match_time,
            report_time)

    def _launch_report(self):
        lv1 = Metrics()
        lv1.add(self.node_perf.attr_lv1).add(self.param_perf.attr_lv1)

        lv2 = Metrics()
        lv2.add(self.node_perf.attr_lv2).add(self.param_perf.attr_lv2)

        lv3 = Metrics()
        lv3.add(self.node_perf.attr_lv3).add(self.param_perf.attr_lv3)

        #diffs = list(self.node_perf.diffs)
        #diffs.extend(self.param_perf.diffs)

        return Report(lv1.as_tuple(), lv2.as_tuple(), lv3.as_tuple(), [])

    def _source_report(self):
        lv1 = Metrics()
        lv1.add(self.pub_perf.attr_lv1).add(self.sub_perf.attr_lv1)
        lv1.add(self.cli_perf.attr_lv1).add(self.srv_perf.attr_lv1)
        lv1.add(self.setter_perf.attr_lv1).add(self.getter_perf.attr_lv1)

        lv2 = Metrics()
        lv2.add(self.pub_perf.attr_lv2).add(self.sub_perf.attr_lv2)
        lv2.add(self.cli_perf.attr_lv2).add(self.srv_perf.attr_lv2)
        lv2.add(self.setter_perf.attr_lv2).add(self.getter_perf.attr_lv2)

        lv3 = Metrics()
        lv3.add(self.pub_perf.attr_lv3).add(self.sub_perf.attr_lv3)
        lv3.add(self.cli_perf.attr_lv3).add(self.srv_perf.attr_lv3)
        lv3.add(self.setter_perf.attr_lv3).add(self.getter_perf.attr_lv3)

        #diffs = list(self.pub_perf.diffs)
        #diffs.extend(self.sub_perf.diffs)
        #diffs.extend(self.cli_perf.diffs)
        #diffs.extend(self.srv_perf.diffs)
        #diffs.extend(self.setter_perf.diffs)
        #diffs.extend(self.getter_perf.diffs)

        return Report(lv1.as_tuple(), lv2.as_tuple(), lv3.as_tuple(), [])

    def _overall_report(self):
        lv1 = Metrics()
        lv1.add(self.node_perf.attr_lv1).add(self.param_perf.attr_lv1)
        lv1.add(self.pub_perf.attr_lv1).add(self.sub_perf.attr_lv1)
        lv1.add(self.cli_perf.attr_lv1).add(self.srv_perf.attr_lv1)
        lv1.add(self.setter_perf.attr_lv1).add(self.getter_perf.attr_lv1)

        lv2 = Metrics()
        lv2.add(self.node_perf.attr_lv2).add(self.param_perf.attr_lv2)
        lv2.add(self.pub_perf.attr_lv2).add(self.sub_perf.attr_lv2)
        lv2.add(self.cli_perf.attr_lv2).add(self.srv_perf.attr_lv2)
        lv2.add(self.setter_perf.attr_lv2).add(self.getter_perf.attr_lv2)

        lv3 = Metrics()
        lv3.add(self.node_perf.attr_lv3).add(self.param_perf.attr_lv3)
        lv3.add(self.pub_perf.attr_lv3).add(self.sub_perf.attr_lv3)
        lv3.add(self.cli_perf.attr_lv3).add(self.srv_perf.attr_lv3)
        lv3.add(self.setter_perf.attr_lv3).add(self.getter_perf.attr_lv3)

        #diffs = list(self.node_perf.diffs)
        #diffs.extend(self.param_perf.diffs)
        #diffs.extend(self.pub_perf.diffs)
        #diffs.extend(self.sub_perf.diffs)
        #diffs.extend(self.cli_perf.diffs)
        #diffs.extend(self.srv_perf.diffs)
        #diffs.extend(self.setter_perf.diffs)
        #diffs.extend(self.getter_perf.diffs)

        return Report(lv1.as_tuple(), lv2.as_tuple(), lv3.as_tuple(), [])


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
    __slots__ = ("attr_lv1", "attr_lv2", "attr_lv3", "diffs")
    resource_type = "Resource"
    snd_attrs = ()

    def report(self, M):
        self._reset()
        self._count_missing(M)
        self._count_spurious(M)
        for u, v in M.matches:
            self._count_rosname(u, v)
            self._count_rostype(u, v)
            self._count_traceability(u, v)
            self._count_secondary_attrs(u, v)
            self._count_conditions(u, v)
        return Report(self.attr_lv1.as_tuple(), self.attr_lv2.as_tuple(),
            self.attr_lv3.as_tuple(), self.diffs)

    def _reset(self):
        self.attr_lv1 = Metrics()
        self.attr_lv2 = Metrics()
        self.attr_lv3 = Metrics()
        self.diffs = []

    def _count_missing(self, M):
        if M.missing:
            # rosname, rostype, traceability, conditions, secondary
            n = 4 + len(self.snd_attrs)
            self.attr_lv1.mis += len(M.missing)
            self.attr_lv2.mis += len(M.missing) * 2
            self.attr_lv3.mis += len(M.missing) * n
            for v in M.missing:
                self._diff(v.rosname, self.resource_type, None, v)

    def _count_spurious(self, M):
        if M.spurious:
            # rosname, rostype, traceability, conditions, secondary
            n = 4 + len(self.snd_attrs)
            self.attr_lv1.spu += len(M.missing)
            self.attr_lv2.spu += len(M.missing) * 2
            self.attr_lv3.spu += len(M.missing) * n
            for u in M.spurious:
                self._diff(u.rosname, self.resource_type, u, None)

    def _count_rosname(self, u, v):
        if u.rosname == v.rosname:
            self.attr_lv1.cor += 1
            self.attr_lv2.cor += 1
            self.attr_lv3.cor += 1
        else:
            if "?" in u.rosname and rosname_match(u.rosname, v.rosname):
                self.attr_lv1.par += 1
                self.attr_lv2.par += 1
                self.attr_lv3.par += 1
            else:
                self.attr_lv1.inc += 1
                self.attr_lv2.inc += 1
                self.attr_lv3.inc += 1
            self._diff(v.rosname, "ROS name", u.rosname, v.rosname)

    def _count_rostype(self, u, v):
        if u.rostype == v.rostype:
            self.attr_lv2.cor += 1
            self.attr_lv3.cor += 1
        else:
            self.attr_lv2.inc += 1
            self.attr_lv3.inc += 1
            self._diff(v.rosname, "ROS type", u.rostype, v.rostype)

    def _count_traceability(self, u, v):
        if u.traceability == v.traceability:
            self.attr_lv3.cor += 1
        else:
            self.attr_lv3.inc += 1
            self._diff(v.rosname, "traceability", u.traceability, v.traceability)

    def _count_conditions(self, u, v):
        cfg1 = u.conditions
        cfg2 = v.conditions
        if not cfg1 and cfg2:
            self.attr_lv3.inc += 1
        elif cfg1 and not cfg2:
            self.attr_lv3.inc += 1
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
                    self.attr_lv3.spu += 1
                elif p > 0:
                    self.attr_lv3.par += 1
                else:
                    self.attr_lv3.inc += 1
            else:
                if p == n:
                    self.attr_lv3.cor += 1
                elif p > 0:
                    self.attr_lv3.par += 1
                else:
                    self.attr_lv3.mis += 1

    def _count_secondary_attrs(self, u, v):
        for attr in self.snd_attrs:
            p = getattr(u, attr)
            g = getattr(v, attr)
            if p == g:
                self.attr_lv3.cor += 1
            else:
                self.attr_lv3.inc += 1
                self._diff(v.rosname, attr.replace("_", " "), p, g)

    def _diff(self, rosname, attr, p, g):
        self.diffs.append(Diff(self.resource_type, rosname, attr, p, g))


class NodePerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Node"
    snd_attrs = ("args",)

class ParamPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Parameter"
    snd_attrs = ("value",)

class PubPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Topic Publisher"
    snd_attrs = ("original_name", "queue_size", "latched",)

class SubPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Topic Subscriber"
    snd_attrs = ("original_name", "queue_size",)

class ClientPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Service Client"
    snd_attrs = ("original_name",)

class ServerPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Service Server"
    snd_attrs = ("original_name",)

class SetterPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Parameter Setter"
    snd_attrs = ("original_name", "value")

class GetterPerformanceEvaluator(PerformanceEvaluator):
    __slots__ = PerformanceEvaluator.__slots__
    resource_type = "Parameter Getter"
    snd_attrs = ("original_name", "value")
