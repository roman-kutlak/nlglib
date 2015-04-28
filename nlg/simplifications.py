import re
from collections import defaultdict

from nlg import prover
from nlg.fol import *


f1 = expr('~P | (~(P & Q) | R)')
f2 = minimise_qm(f1)
f3 = expr('(P & Q) ==> R')


def create_combinations(f, atoms, ops):
    """Return a generator of formulas `f` extended by operators and atoms.
    >>>list(create_combinations(expr('P'), [expr('Q')], LOGIC_OPS))
    [(~ P), (& P, Q), (| P, Q), (==> P, Q), (<== P, Q), (<=> P, Q)]
    
    """
    for op in ops:
        if op == OP_NOT:
            yield (~f)
        else:
            for a in atoms:
                yield Expr(op, f, a)


class Heuristic:
    """Create a new heuristic instance that uses costs from a file
    or a default cost of 1 if the file cannot be read or path is None.
    See `read_costs` for file layout.
    
    """

    def __init__(self, path=None):
        if path:
            self.costs = self.read_costs(path)
        else:
            self.costs = defaultdict(list)
            self.costs['_'].append( ('_', 1) )

    def operator_cost(self, op, context):
        """Return the cost of the operator `op` given the `context`.
        The `context` is just a `str` representation of 
        the formula (eg 'p & q' when the operator is '&').
        
        """
        if op in self.costs:
            for ctx, cost in self.costs[op]:
                if ctx == '_':
                    return cost
                elif re.search(ctx, context):
                    return cost
        # if we got here, the operator is not in the cost dict or
        # it is in the cost dict, but the context did not match
        # so use the default cost
        for ctx, cost in self.costs['_']:
            if ctx == '_':
                return cost

    def formula_cost(self, formula):
        """Return the cost of formula `f` calculated using the heuristic `h`."""
        if formula.args:
            return (self.operator_cost(formula.op, str(formula)) +
                    sum([self.formula_cost(a) for a in formula.args]))
        return 0

    def read_costs(self, path):
        """Read a cost file given by `path` and return a dict with costs. 
        The dictionary has operators as keys and pairs as values.
        The pairs have a string as the first element and a cost (int)
        as the second element.
        E.g., {~: [('[&]', 3), # negation over conjunction has cost 3
                   ('[|]', 2), # negation over disjunction has cost 2
                   ('_', 1)]}  # negation in any other context has cost 1
        The "don't care" pattern is the underscore. If an op is not in
        the dict, use the default value, which is 1 unless specified by
        the pattern _ _ n.
        
        """
        result = defaultdict(list)
        with open(path, 'r') as f:
            for line in f:
                text = line.partition('#')[0].strip() # allow comments '#'
                if not text:
                    continue
                op, ctx, cost = text.split()
                p = (ctx, int(cost))
                result[op].append(p)
        # note that the costs are checked in the same order in which they are
        # specified in the file. If the user specified the default cost, this
        # will still use the user's choice instead of the default below.
        result['_'].append( ('_', 1) ) # (default cost 1)
        return result


def bfs(f, h, operators, max=0):
    """Return the best formula given a heuristic `h`. """
    if max == 0:
        max = h.formula_cost(f)
    closed = set()
    atoms = sorted(collect_propositions(f), key=lambda x: str(x))
    queue = atoms[:]
    best = None
    best_cost = max if max > 0 else 1000
    while queue:
        current = queue.pop(0)
        if h.formula_cost(current) < best_cost:
            if prover.test_equivalent(f, current, []):
                best = current
                best_cost = h.formula_cost(best)
                if (max == -1):
                    return best
        new = [n for n in create_combinations(current, atoms, operators)
            if h.formula_cost(n) < best_cost and n not in closed]
        queue.extend(new)
        closed.update(new)
    return best or f




#############################################################################
##
## Copyright (C) 2015 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################
