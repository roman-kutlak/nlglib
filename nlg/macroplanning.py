from nlg.fol import OP_NOT, OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY
from nlg.fol import OP_EQUALS, OP_NOTEQUALS, OP_EQUIVALENT
from nlg.fol import OP_EXISTS, OP_FORALL
from nlg.fol import is_predicate, is_variable, is_function

from nlg.structures import Message, MsgSpec, Word, PlaceHolder, NounPhrase
from nlg.structures import DiscourseContext, OperatorContext



import logging

def get_log():
    return logging.getLogger(__name__)


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
            if ('NEGATION' in self._features and
                self._features['NEGATION'] == 'TRUE'):
                    neg = 'not '
            return(neg + p.op + '(' + ', '.join([str(x) for x in p.args]) + ')')

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
                msg = 'Expected N or type_N in replacing a PlaceHolder ' \
                'but received ' + str(param)
                raise SignatureError(msg)

        if idx >= len(self.predicate.args):
            msg = 'Requested index (' + str(idx) + ') larger than '\
            'number of variables in predicate "' + str(self.predicate) + '"'
            raise SignatureError(msg)

        parameter = self.predicate.args[idx]
        result = None
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
            neg = ''
            if ('NEGATION' in self._features and
                self._features['NEGATION'] == 'TRUE'):
                    neg = 'not '
            return(neg + p.op + '(' + ', '.join([str(x) for x in p.args]) + ')')

    def value_for(self, idx):
        """ Return a replacement for a placeholder with id param.
        The function returns the type for type_N and the name of the variable
        for N at position N or throws SignatureError.

        """
        if idx >= len(self.args):
            msg = 'Requested index (' + str(idx) + ') larger than '\
            'number of variables in predicate "' + str(self.predicate) + '"'
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
        test = lambda x: (x.op == '&' or x.op == '|')
        if any(map(test, f.args)):
            m.marker = ', and'
        else:
            m.marker = 'and'
        return m
    if f.op == OP_OR:
        msgs = [formula_to_rst(x) for x in f.args]
        m = Message('Disjunction', None, *msgs)
        test = lambda x: (x.op != 'forall' and
                          x.op != 'exists')
        if any(map(test, f.args)):
            m.marker = ', or'
        else:
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
    if f.op[0] == OP_NOT and is_predicate(f.args[0]):
        get_log().debug('negated predicate: ' + str(f))
        arg = f.args[0]
        m = PredicateMsg(arg, *[formula_to_rst(x) for x in arg.args])
        m._features = {'NEGATION': 'TRUE'}
        return m
    if f.op[0] == OP_NOT and is_variable(f.args[0]):
        get_log().debug('negated variable: ' + str(f))
        arg = f.args[0]
        m = NounPhrase(PlaceHolder(arg.op), Word('not', 'DETERMINER'))
        return m
    if f.op[0] == OP_NOT:
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
        return PlaceHolder(f.op)


def fol_to_synt(f, do_parent=True):
    """ FOL formula to syntactic structure. """
    get_log().debug('fol_to_synt({0}).'.format(str(f)))




#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
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
