import itertools

import nltk
from nltk.sem import *
from nltk.sem.logic import *

from .struct import RhetRel, PredicateMsg, StringMsg, Document

from nlglib.microplanning import NounPhrase, Word, Var

from nlglib.features import NEGATED

expr = nltk.sem.Expression.fromstring


def preprocess_content(data, **_):
    if isinstance(data, str):
        formulas = [expr(f) for f in data.split(';') if f.strip()]
    elif hasattr(data, '__iter__'):
        formulas = [expr(f) if isinstance(f, str) else f for f in data]
    else:
        formulas = data
    rv = [f.simplify() for f in formulas]
    return rv


def select_content(formulas, **_):
    rv = []
    for item in formulas:
        rv.append(formula_to_rst(item))
    return rv


def aggregate_content(items, **_):
    if isinstance(items, (list, tuple)):
        if len(items) > 1:
            # order predicates for aggregation (e.g., clause, mod, mod)
            subj_groups = defaultdict(list)
            for item in items:
                if hasattr(item, 'args') and list(item.args):
                    first = str(list(item.args)[0])
                    subj_groups[first].append(item)
                else:
                    subj_groups[None].append(item)
            # put the longest list of predicates first
            by_length = sorted(subj_groups.values(), key=lambda x: len(x), reverse=True)
            for group in by_length:
                group.sort(key=lambda x: len(x.args if hasattr(x, 'args') else []), reverse=True)
            new_items = list(itertools.chain(*by_length))
            rv = RhetRel('Sequence', *new_items)
        else:
            rv = items[0]
    else:
        rv = items
    return rv


def structure_content(items, **_):
    if isinstance(items, (list, tuple)):
        rv = Document(None, *items)
    else:
        rv = Document(None, items)
    return rv


def formula_to_rst(f):
    """ Convert a FOL formula to an RST tree. """
    # TODO: handle inequality better
    # TODO: handle lambdas (use Var?)
    if isinstance(f, AndExpression):
        first = formula_to_rst(f.first)
        second = formula_to_rst(f.second)
        m = RhetRel('Conjunction', first, second)
        m.marker = 'and'
        return m
    if isinstance(f, OrExpression):
        first = formula_to_rst(f.first)
        second = formula_to_rst(f.second)
        m = RhetRel('Disjunction', first, second)
        m.marker = 'or'
        return m
    if isinstance(f, ImpExpression):
        first = formula_to_rst(f.first)
        second = formula_to_rst(f.second)
        m = RhetRel('Imply', first, satellite=second)
        return m
    if isinstance(f, IffExpression):
        first = formula_to_rst(f.first)
        second = formula_to_rst(f.second)
        m = RhetRel('Equivalent', first, satellite=second)
        return m
    if isinstance(f, EqualityExpression):
        first = formula_to_rst(f.first)
        second = formula_to_rst(f.second)
        m = RhetRel('Equality', first, satellite=second)
        return m
    # if isinstance(f, EqualityExpression):
    #     first = formula_to_rst(f.first)
    #     second = formula_to_rst(f.second)
    #     m = RhetRel('Inequality', *msgs[:-1], satellite=msgs[-1])
    #     return m
    if isinstance(f, AllExpression):
        first = formula_to_rst(f.variable)
        second = formula_to_rst(f.second)
        m = RhetRel('Quantifier', first, second)
        m.marker = 'for all'
        return m
    if isinstance(f, ExistsExpression):
        first = formula_to_rst(f.variable)
        second = formula_to_rst(f.second)
        m = RhetRel('Quantifier', first, second)
        m.marker = 'there exists'
        return m
    if isinstance(f, NegatedExpression) and isinstance(f.term, ApplicationExpression):
        predicate = f.term
        m = PredicateMsg(predicate.pred.variable.name,
                         *[formula_to_rst(x) for x in predicate.args],
                         features=(NEGATED.true, ))
        return m
    if isinstance(f, NegatedExpression) and isinstance(f.term, IndividualVariableExpression):
        arg = f.term
        m = NounPhrase(Var(arg.variable.name), Word('not', 'DETERMINER'))
        return m
    if isinstance(f, NegatedExpression) and isinstance(f.term, Expression):
        arg = formula_to_rst(f.term)
        m = RhetRel('Negation', arg)
        m.marker = 'it is not the case that'
        return m
    if isinstance(f, NegatedExpression):
        raise NotImplementedError()
    if isinstance(f, ApplicationExpression):
        return PredicateMsg(f.pred.variable.name, *[formula_to_rst(x) for x in f.args])
    if isinstance(f, (IndividualVariableExpression, ConstantExpression)):
        m = NounPhrase(Var(f.variable.name))
        return m
    else:
        return StringMsg(str(f))
