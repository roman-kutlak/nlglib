import itertools
import logging
from collections import defaultdict

from nlglib.logic.fol import OP_EQUALS, OP_NOTEQUALS, OP_EQUIVALENT
from nlglib.logic.fol import OP_EXISTS, OP_FORALL
from nlglib.logic.fol import OP_NOT, OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY
from nlglib.logic.fol import expr
from nlglib.logic.fol import is_predicate, is_variable, is_function
from nlglib.logic.simplifications import simplification_ops
from nlglib.structures import RhetRel, PredicateMsg, Word, Var
from nlglib.structures import NounPhrase, Document


logger = logging.getLogger(__name__)


def preprocess_content(data, **kwargs):
    simplifications = kwargs.get('simplifications', [])
    if isinstance(data, str):
        formulas = [expr(f) for f in data.split(';') if f.strip()]
    elif hasattr(data, '__iter__'):
        formulas = [expr(f) if isinstance(f, str) else f for f in data]
    else:
        formulas = data
    rv = []
    for f in formulas:
        for s in filter(lambda x: x in simplification_ops, simplifications):
            f = simplification_ops[s](f)
        rv.append(f)
    return rv


def select_content(formulas, **_):
    rv = []
    for item in formulas:
        rv.append(formula_to_rst(item))
    return rv


def aggregate_content(items, **_):
    if isinstance(items, (list, tuple)):
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
        rv = Message('Sequence', None, *new_items)
    else:
        rv = items
    return rv


def structure_content(items, **_):
    if isinstance(items, (list, tuple)):
        rv = Document(*items)
    else:
        rv = Document(items)
    return rv


def formula_to_rst(f):
    """ Convert a FOL formula to an RST tree. """
    logger.debug(str(f))
    if f.op == OP_AND:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Conjunction', *msgs)
        m.marker = 'and'
        return m
    if f.op == OP_OR:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Disjunction', *msgs)
        m.marker = 'or'
        return m
    if f.op == OP_IMPLIES:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Imply', msgs[0], satellite=msgs[1])
        return m
    if f.op == OP_IMPLIED_BY:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('ImpliedBy', msgs[0], satellite=msgs[1])
        return m
    if f.op == OP_EQUIVALENT:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Equivalent', msgs[0], satellite=msgs[1])
        return m
    if f.op == OP_EQUALS:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Equality', *msgs[:-1], satellite=msgs[-1])
        return m
    if f.op == OP_NOTEQUALS:
        msgs = [formula_to_rst(x) for x in f.args]
        m = RhetRel('Inequality', *msgs[:-1], satellite=msgs[-1])
        return m
    if f.op == OP_FORALL:
        vars = [formula_to_rst(x) for x in f.vars]
        msgs = [formula_to_rst(x) for x in f.args]
        if len(msgs) > 1:
            raise ValueError('Too many arguments for quantifier.')
        nucleus = RhetRel('List', *vars)
        m = RhetRel('Quantifier', nucleus, satellite=msgs[0])
        m.marker = 'for all'
        return m
    if f.op == OP_EXISTS:
        vars = [formula_to_rst(x) for x in f.vars]
        msgs = [formula_to_rst(x) for x in f.args]
        if len(msgs) > 1:
            raise ValueError('Too many arguments for quantifier.')
        nucleus = RhetRel('List', *vars)
        m = RhetRel('Quantifier', nucleus, satellite=msgs[0])
        if len(f.vars) == 1:
            m.marker = 'there exists'
        else:
            m.marker = 'there exist'
        return m
    if f.op == OP_NOT and is_predicate(f.args[0]):
        logger.debug('negated predicate: ' + str(f))
        arg = f.args[0]
        m = PredicateMsg(arg, *[formula_to_rst(x) for x in arg.args])
        m.features = {'NEGATED': 'true'}
        return m
    if f.op == OP_NOT and is_variable(f.args[0]):
        logger.debug('negated variable: ' + str(f))
        arg = f.args[0]
        m = NounPhrase(Var(arg.op), Word('not', 'DETERMINER'))
        return m
    if f.op == OP_NOT:
        logger.debug('negated formula: ' + str(f))
        msgs = [formula_to_rst(x) for x in f.args]
        if len(msgs) > 1:
            m = RhetRel('Negation', msgs[:-1], satellite=msgs[-1])
        else:
            m = RhetRel('Negation', msgs[0])
        m.marker = 'it is not the case that'
        return m
    if is_predicate(f):
        logger.debug('predicate: ' + str(f))
        return PredicateMsg(f, *[formula_to_rst(x) for x in f.args])
    if is_function(f):
        logger.debug('function: ' + str(f))
        return Var(f.op, PredicateMsg(f, *[formula_to_rst(x) for x in f.args]))
    else:
        logger.debug('None: ' + repr(f))
        return PredicateMsg(f)
