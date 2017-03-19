import logging

from nlglib.fol import OP_EQUALS, OP_NOTEQUALS, OP_EQUIVALENT
from nlglib.fol import OP_EXISTS, OP_FORALL
from nlglib.fol import OP_NOT, OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY
from nlglib.fol import is_predicate, is_variable, is_function
from nlglib.structures import Message, MsgSpec, Word, String, PlaceHolder
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
    return items


def structure_content(items, **kwargs):
    rv = Paragraph(*items)
    return rv


class SignatureError(Exception):
    pass


# TODO: deprecate?
class PredicateMsgSpec(MsgSpec):
    """ This class is used for instantiating Predicate as message spec. """

    def __init__(self, pred, features=None):
        """ Keep a reference to the corresponding predicate so that
        we can look up arguments for any variables.

        """
        super().__init__('{0}/{1}'.format(pred.op, len(pred.args)))
        self.predicate = pred
        self._features = features or {}

    def __str__(self):
        """ Return a suitable string representation. """
        p = self.predicate
        if len(p.args) == 0:
            return p.op
        else:
            neg = ''
            if 'NEGATED' in self._features and self._features['NEGATED'] == 'true':
                neg = 'not '
            return neg + p.op + '(' + ', '.join([str(x) for x in p.args]) + ')'

    def value_for(self, param):
        """ Return a replacement for a placeholder with id param.
        Predicates have two types of parameters - type_N and var_N, which
        correspond to the type and variable on position N respectively
        (e.g., ?pkg - package).
        The function returns the type for type_N and the name of the variable
        for N at position N or throws SignatureError.

        """
        idx = -1
        try:
            idx = int(param)
        except Exception:
            try:
                tmp = param.partition('_')
                idx = tmp[2]
            except:
                msg = 'Expected N or type_N in replacing a PlaceHolder but received ' + str(param)
                raise SignatureError(msg)

        if idx >= len(self.predicate.args):
            msg = ('Requested index (' + str(idx) +
                   ') larger than number of variables in predicate "' + str(self.predicate) + '"')
            raise SignatureError(msg)

        parameter = self.predicate.args[idx]
        if param.startswith('type'):
            result = Word(parameter.op, 'NOUN')
        elif param.startswith('var'):
            result = Word(parameter.op, 'NOUN')
        else:
            result = PlaceHolder(parameter.op)
        return result


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
        """ Return a replacement for a placeholder with id param.
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
        #        test = lambda x: (x.op == '&' or x.op == '|')
        #        if any(map(test, f.args)):
        #            m.marker = ', and'
        #        else:
        m.marker = 'and'
        return m
    if f.op == OP_OR:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Disjunction', None, *msgs)
        #        test = lambda x: (x.op != 'forall' and
        #                          x.op != 'exists')
        #        if any(map(test, f.args)):
        #            m.marker = ', or'
        #        else:
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
        m = NounPhrase(PlaceHolder(arg.op), Word('not', 'DETERMINER'))
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
        return PlaceHolder(f.op,
                           PredicateMsg(f, *[formula_to_rst(x) for x in f.args]))
    else:
        get_log().debug('None: ' + repr(f))
        return PredicateMsg(f)


def fol_to_synt(f, do_parent=True):
    """ FOL formula to syntactic structure. """
    get_log().debug('fol_to_synt({0}).'.format(str(f)))
