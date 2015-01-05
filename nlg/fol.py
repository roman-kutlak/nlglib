import numbers
from pyparsing import (nums, alphas, alphanums, restOfLine,
                       Word, Group, Optional, Forward, Keyword, Literal,
                       Suppress, opAssoc, operatorPrecedence, delimitedList,
                       ParserElement, ParseException, ParseSyntaxException)
import logging

def get_log():
    return logging.getLogger(__name__)


#______________________________________________________________________________

OP_NOT = '~'
OP_OR  = '|'
OP_AND = '&'

OP_EQUALS     = '%'
OP_NOTEQUALS  = '^'

OP_IMPLIES    = '>>'
OP_IMPLIED_BY = '<<'
OP_EQUIVALENT = '<->'

OP_FORALL = 'forall'
OP_EXISTS = 'exists'

OP_TRUE   = 'TRUE'
OP_FALSE  = 'FALSE'


# ∀ ?x: Happy(?x) ⇔ ¬Sad(?x)
OPS = {
    'not'    : OP_NOT,
    '\u00AC' : OP_NOT,
    'equals' : OP_EQUALS,
    '='      : OP_EQUALS,
    'notequals' : OP_NOTEQUALS,
    '=/='    : OP_NOTEQUALS,
    '\u2260' : OP_NOTEQUALS,
    'and'    : OP_AND,
    '\u2227' : OP_AND,
    'or'     : OP_OR,
    '\u2228' : OP_OR,
    'implies' : OP_IMPLIES,
    '->'      : OP_IMPLIES,
    '\u2192'  : OP_IMPLIES,
    'impliedby' : OP_IMPLIED_BY,
    '<-'        : OP_IMPLIED_BY,
    '\u2190'    : OP_IMPLIED_BY,
    '\u2194'    : OP_EQUIVALENT,
    '\u2200'    : OP_FORALL,
    '\u2203'    : OP_EXISTS
}


# Class based on the code accompanying AI: a modern approach.
class Expr:
    """A symbolic mathematical expression.  We use this class for logical
    expressions, and for terms within logical expressions. In general, an
    Expr has an op (operator) and a list of args.  The op can be:
      Null-ary (no args) op:
        A number, representing the number itself.  (e.g. Expr(42) => 42)
        A symbol, representing a variable or constant (e.g. Expr('F') => F)
      Unary (1 arg) op:
        '~', '-', representing NOT, negation (e.g. Expr('~', Expr('P')) => ~P)
      Binary (2 arg) op:
        '>>', '<<', representing forward and backward implication
        '**' representing biconditional (logical equivalence)
        '+', '-', '*', '/' representing arithmetic operators
        '<', '>', '>=', '<=', representing comparison operators
        '<=>', '^', representing logical equality and XOR
      N-ary (0 or more args) op:
        '&', '|', representing conjunction and disjunction
        A symbol, representing a function term or FOL proposition

    Exprs can be constructed with operator overloading: if x and y are Exprs,
    then so are x + y and x & y, etc.
    
    WARNING: x == y and x != y are NOT Exprs.  The reason is that we want
    to write code that tests 'if x == y:' and if x == y were the same
    as Expr('==', x, y), then the result would always be true; not what a
    programmer would expect.  But we still need to form Exprs representing
    equalities and disequalities.  We concentrate on logical equality (or
    equivalence) and logical disequality (or XOR).  You have 3 choices:
        (1) Expr('<=>', x, y) and Expr('^', x, y)
            Note that ^ is bitwose XOR in Python (and Java and C++)
        (2) expr('x <=> y') and expr('x =/= y').
            See the doc string for the function expr.
        (3) (x % y) and (x ^ y).
            It is very ugly to have (x % y) mean (x <=> y), but we need
            SOME operator to make (2) work, and this seems the best choice.

    WARNING: if x is an Expr, then so is x + 1, because the int 1 gets
    coerced to an Expr by the constructor.  But 1 + x is an error, because
    1 doesn't know how to add an Expr.  (Adding an __radd__ method to Expr
    wouldn't help, because int.__add__ is still called first.) Therefore,
    you should use Expr(1) + x instead, or ONE + x, or expr('1 + x').
    """

    def __init__(self, op, *args):
        "Op is a string or number; args are Exprs (or are coerced to Exprs)."
        assert isinstance(op, str) or (isnumber(op) and not args)
        self.op = num_or_str(op)
        self.args = list(map(to_expr, args)) ## Coerce args to Exprs

    def __repr__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        if not self.args:         # Constant or proposition with arity 0
            return str(self.op)
        elif is_prop_symbol(self.op):  # Functional or propositional operator
            return '%s(%s)' % (self.op, ', '.join(map(repr, self.args)))
        elif len(self.args) == 1: # Prefix operator
            return self.op + repr(self.args[0])
        else:                     # Infix operator
            return '(%s)' % (' '+self.op+' ').join(map(repr, self.args))

    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return (other is self) or (isinstance(other, Expr)
            and self.op == other.op and self.args == other.args)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.args))

    # Some operators implemented for convenience
    def __neg__(self):           return Expr('-',  self)
    def __lt__(self, other):     return Expr('<',  self, other)
    def __le__(self, other):     return Expr('<=', self, other)
    def __ge__(self, other):     return Expr('>=', self, other)
    def __gt__(self, other):     return Expr('>',  self, other)
    def __add__(self, other):    return Expr('+',  self, other)
    def __sub__(self, other):    return Expr('-',  self, other)
    def __mul__(self, other):    return Expr('*',  self, other)
    def __div__(self, other):    return Expr('/',  self, other)
    def __truediv__(self, other):return Expr('/',  self, other)
    
    def __invert__(self):        return Expr(OP_NOT,  self)
    def __and__(self, other):    return Expr(OP_AND,  self, other)
    def __or__(self, other):     return Expr(OP_OR,  self, other)
    
    def __lshift__(self, other): return Expr(OP_IMPLIED_BY, self, other)
    def __rshift__(self, other): return Expr(OP_IMPLIES, self, other)
    def __pow__(self, other):    return Expr(OP_EQUIVALENT, self, other)
    
    def __mod__(self, other):    return Expr(OP_EQUALS,  self, other)
    def __xor__(self, other):    return Expr(OP_NOTEQUALS,  self, other)


class Quantifier(Expr):
    """ Quantified expression is an expression that contains variables. """

    def __init__(self, op, vars, *args):
        super(Quantifier, self).__init__(op, *args)
        self.vars = list(map(to_expr, vars))

    def __repr__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        return '{0} {1}: ({2})'.format(self.op,
                                ', '.join(map(repr, self.vars)),
                                ', '.join(map(repr, self.args)))

    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return ((other is self) or
                (isinstance(other, Expr) and
                 self.op == other.op and
                 self.vars == other.vars and
                 self.args == other.args))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.vars)) ^ hash(tuple(self.args))


def is_symbol(s):
    "A string s is a symbol if it starts with an alphabetic char."
    return isinstance(s, str) and s[:1].islower()


def is_var_symbol(s):
    "A logic variable symbol is an initial-lowercase string."
    return isinstance(s, str) and s[:1] == '?'


def is_prop_symbol(s):
    """A proposition logic symbol is an initial-uppercase string other than
    TRUE or FALSE."""
    return (isinstance(s, str) and s[0].isupper() and
            s != 'TRUE' and s != 'FALSE')


def variables(s):
    """Return a set of the variables in expression s.
    >>> ppset(variables(F(x, A, y)))
    set([x, y])
    >>> ppset(variables(F(G(x), z)))
    set([x, z])
    >>> ppset(variables(expr('F(x, x) & G(x, y) & H(y, z) & R(A, z, z)')))
    set([x, y, z])
    """
    result = set([])
    def walk(s):
        if is_variable(s):
            result.add(s)
        else:
            for arg in s.args:
                walk(arg)
    walk(s)
    return result


def num_or_str(x):
    """The argument is a string; convert to a number if possible, or strip it.
    >>> num_or_str('42')
    42
    >>> num_or_str(' 42x ')
    '42x'
    """
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return str(x).strip()


# #############################  PARSING  ################################### #


# code nicked from the book Programming in Python 3 (kindle)
# optimisation -- before creating any parsing elements
ParserElement.enablePackrat()

def get_op(x):
    if x in OPS: return OPS[x]
    return x

def to_expr(item):
    get_log().debug('to_expr: ' + str((repr(type(item)), repr(item))))
    if isinstance(item, str): return Expr(item)
    if isinstance(item, numbers.Number): return Expr(item)
    if isinstance(item, Expr): return item
    if hasattr(item, '__getitem__'): return list(map(to_expr, item))
    return item.to_expr()


class FOLQuant:
    def __init__(self, t):
        tmp = t[0].asDict()
        self.op = get_op(tmp['quantifier'])
        self.vars = tmp['vars'].asList()
        self.args = [tmp['args']]

    def __str__(self):
        vars = ', '.join(self.vars)
        return("%s %s: (" % (self.op, vars)) + ''.join(map(str,self.args)) + ")"

    __repr__ = __str__

    def to_expr(self):
        return Quantifier(self.op, [Expr(v) for v in self.vars], *self.args)


class FOLBinOp:
    def __init__(self,t):
        self.op = get_op(t[0][1])
        self.args = t[0][0::2]
        
    def __str__(self):
        sep = " %s " % self.op
        return "(" + sep.join(map(str,self.args)) + ")"
    
    __repr__ = __str__
        
    def to_expr(self):
        return Expr(self.op, *self.args)


class FOLUnOp:
    def __init__(self,t):
        self.op = get_op(t[0][0])
        self.args = to_expr(t[0][1])
        
    def __str__(self):
        return (str(self.op) + "(" + str(self.args) + ")")

    __repr__ = __str__

    def to_expr(self):
        return Expr(self.op, self.args)


class FOLPred:
    def __init__(self,t):
        self.op = get_op(t[0][0])
        self.args = t[0][1]
        
    def __str__(self):
        return (str(self.op) + "(" + ', '.join(map(str,self.args)) + ")")

    __repr__ = __str__

    def to_expr(self):
        return Expr(self.op, *self.args)

left_parenthesis, right_parenthesis = map(Suppress, '()')
forall = Keyword('forall') | Literal('\u2200')
exists = Keyword('exists') | Literal('\u2203')
implies = Literal('->') | Keyword('implies') | Literal('\u2192')
implied = Literal('<-') | Keyword('impliedby') | Literal('\u2190')
iff = Literal('<->') | Keyword('iff') | Literal('\u2194')
or_  = Literal('|') | Keyword('or') | Literal('\u2228')
and_ = Literal('&') | Keyword('and') | Literal('\u2227')
not_ = Literal('~') | Keyword('not') | Literal('\u00AC')
equals = Literal('=') | Keyword('equals')
notequals = Literal('=/=') | Keyword('notequals') | Literal('\u2260')
boolean = Keyword('false') | Keyword('true')
colon = Literal(':').suppress()
symbol = Word(alphas + '?', alphanums)
#
term = Forward() # definition of term will involve itself
term << (Group(symbol + Group(left_parenthesis +
                              delimitedList(term) +
                              right_parenthesis)).setParseAction(FOLPred) |
         symbol)

# allow python style comments
comment = (Literal('#') + restOfLine).suppress()

# main parser for FOL formula
formula = Forward()
formula.ignore(comment)
forall_expression = Group(forall.setResultsName("quantifier") +
                      delimitedList(symbol).setResultsName("vars") + colon +
                      formula.setResultsName("args")).setParseAction(FOLQuant)
exists_expression = Group(exists.setResultsName("quantifier") +
                      delimitedList(symbol).setResultsName("vars") + colon +
                      formula.setResultsName("args")).setParseAction(FOLQuant)

operand = forall_expression | exists_expression | boolean | term

# specify the precedence -- highest precedence first, lowest last
formula << operatorPrecedence(operand, [(equals, 2, opAssoc.LEFT, FOLBinOp),
                                        (notequals, 2, opAssoc.LEFT, FOLBinOp),
                                        (not_, 1, opAssoc.RIGHT, FOLUnOp),
                                        (and_, 2, opAssoc.LEFT, FOLBinOp),
                                        (or_, 2, opAssoc.LEFT, FOLBinOp),
                                        (implies, 2, opAssoc.RIGHT, FOLBinOp),
                                        (implied, 2, opAssoc.RIGHT, FOLBinOp),
                                        (iff, 2, opAssoc.RIGHT, FOLBinOp)])
# error handling -- consider
#>>> def oops(s, loc, expr, err):
#...     print ("s={0!r} loc={1!r} expr={2!r}\nerr={3!r}".format(
#...            s, loc, expr, err))
#... 
#>>> fail = pp.NoMatch().setName('fail-parser').setFailAction(oops)
#>>> r = fail.parseString("None shall pass!")
#s='None shall pass!' loc=0 expr=fail-parser
#err=Expected fail-parser (at char 0), (line:1, col:1)
#pyparsing.ParseException: Expected fail-parser (at char 0), (line:1,
#col:1)

###


class FormulaParseError(Exception):
    pass


def parse_formula(s):
    """ Parse the string s representing a formula and return it as an Expr. """
    try:
        result = formula.parseString(s, parseAll=True)
        return to_expr(result[0])
    except (ParseException, ParseSyntaxException) as err:
        msg=("Syntax error: {0!r}\n{0.line}\n{1}^".\
             format(err, " " * (err.column)))
        raise FormulaParseError(msg)
