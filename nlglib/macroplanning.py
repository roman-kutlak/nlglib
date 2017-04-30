import itertools
import logging

from collections import defaultdict

from nlglib.fol import OP_EQUALS, OP_NOTEQUALS, OP_EQUIVALENT
from nlglib.fol import OP_EXISTS, OP_FORALL
from nlglib.fol import OP_NOT, OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY
from nlglib.fol import is_predicate, is_variable, is_function
from nlglib.structures import Message, MsgSpec, Word, String, Var
from nlglib.structures import NounPhrase, Paragraph
from nlglib.fol import expr
from nlglib.simplifications import simplification_ops


def get_log():
    return logging.getLogger(__name__)


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


def select_content(formulas, **kwargs):
    rv = []
    for item in formulas:
        rv.append(formula_to_rst(item))
    return rv


def aggregate_content(items, **kwargs):
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
        rv =Message('Sequence', None, *new_items)
    else:
        rv = items
    return rv


def structure_content(items, **kwargs):
    if isinstance(items, (list, tuple)):
        rv = Paragraph(*items)
    else:
        rv = Paragraph(items)
    return rv


class SignatureError(Exception):
    pass


class PredicateMsg(MsgSpec):
    """ This class is used for instantiating Predicate as message spec. """

    def __init__(self, pred, *arguments, features=None):
        """ Representation of a predicate.
        """
        super().__init__(str(pred.op))
        self.predicate = pred
        self.args = list(arguments)
        self._features = features or {}

    def __str__(self):
        """ Return a suitable string representation. """
        p = self.predicate
        if len(p.args) == 0:
            return p.op
        else:
            return p.op + '(' + ', '.join([str(x) for x in p.args]) + ')'

    def __repr__(self):
        """ Return a suitable string representation. """
        p = self.predicate
        if len(p.args) == 0:
            return p.op
        else:
            neg = ''
            if 'NEGATED' in self._features and self._features['NEGATED'] == 'true':
                neg = 'not '
            return neg + p.op + '(' + ', '.join([str(x) for x in p.args]) + ')'

    def value_for(self, idx):
        """ Return a replacement for a var with id param.
        The function returns the type for type_N and the name of the variable
        for N at position N or throws SignatureError.

        """
        if idx >= len(self.args):
            msg = ('Requested index (' +
                   str(idx) + ') larger than number of variables in predicate "' + str(self.predicate) + '"')
            raise SignatureError(msg)

        return self.args[idx]


class StringMsgSpec(MsgSpec):
    """ Use this as a simple message that contains canned text. """

    def __init__(self, text):
        super().__init__('simple_message')
        self.text = text

    def value_for(self, _):
        return String(self.text)


def formula_to_rst(f):
    """ Convert a FOL formula to an RST tree. """
    get_log().debug(str(f))
    if f.op == OP_AND:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Conjunction', None, *msgs)
        m.marker = 'and'
        return m
    if f.op == OP_OR:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Disjunction', None, *msgs)
        m.marker = 'or'
        return m
    if f.op == OP_IMPLIES:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Imply', msgs[0], msgs[1])
        return m
    if f.op == OP_IMPLIED_BY:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Imply', msgs[1], msgs[0])
        return m
    if f.op == OP_EQUIVALENT:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Equivalent', msgs[0], msgs[1])
        return m
    if f.op == OP_EQUALS:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Equality', msgs[0], *msgs[1:])
        return m
    if f.op == OP_NOTEQUALS:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Inequality', msgs[0], *msgs[1:])
        return m
    if f.op == OP_FORALL:
        vars = [formula_to_rst(x) for x in f.vars]
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Quantifier', vars, *msgs)
        m.marker = 'for all'
        return m
    if f.op == OP_EXISTS:
        vars = [formula_to_rst(x) for x in f.vars]
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Quantifier', vars, *msgs)
        if len(f.vars) == 1:
            m.marker = 'there exists'
        else:
            m.marker = 'there exist'
        return m
    if f.op == OP_NOT and is_predicate(f.args[0]):
        get_log().debug('negated predicate: ' + str(f))
        arg = f.args[0]
        m = PredicateMsg(arg, *[formula_to_rst(x) for x in arg.args])
        m._features = {'NEGATED': 'true'}
        return m
    if f.op == OP_NOT and is_variable(f.args[0]):
        get_log().debug('negated variable: ' + str(f))
        arg = f.args[0]
        m = NounPhrase(Var(arg.op), Word('not', 'DETERMINER'))
        return m
    if f.op == OP_NOT:
        get_log().debug('negated formula: ' + str(f))
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Negation', msgs[0], *msgs[1:])
        m.marker = 'it is not the case that'
        return m
    if is_predicate(f):
        get_log().debug('predicate: ' + str(f))
        return PredicateMsg(f, *[formula_to_rst(x) for x in f.args])
    if is_function(f):
        get_log().debug('function: ' + str(f))
        return Var(f.op,
                           PredicateMsg(f, *[formula_to_rst(x) for x in f.args]))
    else:
        get_log().debug('None: ' + repr(f))
        return PredicateMsg(f)


def fol_to_synt(f, do_parent=True):
    """ FOL formula to syntactic structure. """
    get_log().debug('fol_to_synt({0}).'.format(str(f)))
