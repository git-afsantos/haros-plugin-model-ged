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
# Notice
###############################################################################

# This algorithm is missing in networkx version 2.2 (used in Python 2.7).
# I am just copying the algorithm here.
# https://github.com/networkx/networkx/blob/c91c0cd93759d0c6ad21e23fbe3d4290d2ed0d21/networkx/algorithms/bipartite/matching.py#L477


###############################################################################
# Imports
###############################################################################

import itertools

from networkx.algorithms.bipartite.matrix import biadjacency_matrix
from networkx.algorithms.bipartite import sets as bipartite_sets
import networkx as nx


###############################################################################
# Algorithm
###############################################################################

def minimum_weight_full_matching(G, top_nodes=None, weight='weight'):
    try:
        import scipy.optimize
    except ImportError:
        raise ImportError('minimum_weight_full_matching requires SciPy: ' +
                          'https://scipy.org/')
    left, right = nx.bipartite.sets(G, top_nodes)
    # Ensure that the graph is complete. This is currently a requirement in
    # the underlying  optimization algorithm from SciPy, but the constraint
    # will be removed in SciPy 1.4.0, at which point it can also be removed
    # here.
    for (u, v) in itertools.product(left, right):
        # As the graph is undirected, make sure to check for edges in
        # both directions
        if (u, v) not in G.edges() and (v, u) not in G.edges():
            raise ValueError('The bipartite graph must be complete.')
    U = list(left)
    V = list(right)
    weights = biadjacency_matrix(G, row_order=U,
                                 column_order=V, weight=weight).toarray()
    left_matches = scipy.optimize.linear_sum_assignment(weights)
    d = {U[u]: V[v] for u, v in zip(*left_matches)}
    # d will contain the matching from edges in left to right; we need to
    # add the ones from right to left as well.
    d.update({v: u for u, v in d.items()})
    return d
