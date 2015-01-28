import numbers
from pyparsing import (nums, alphas, alphanums, restOfLine, Word,
                       Group, Optional, Keyword, Literal, CaselessKeyword,
                       Combine, Forward, Suppress, opAssoc, operatorPrecedence,
                       delimitedList, oneOf, ParserElement,
                       ParseException, ParseSyntaxException)
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

LOGIC_OPS = [OP_NOT, OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY, OP_EQUIVALENT]
UNARY_LOGIC_OPS = [OP_NOT]
BINARY_LOGIC_OPS = [OP_AND, OP_OR, OP_IMPLIES, OP_IMPLIED_BY, OP_EQUIVALENT]
BINARY_OPS = BINARY_LOGIC_OPS + [OP_EQUALS, OP_NOTEQUALS]
CONDITIONAL_LOGIC_OPS = [OP_IMPLIES, OP_IMPLIED_BY, OP_EQUIVALENT]

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
    '==>'     : OP_IMPLIES,
    '\u2192'  : OP_IMPLIES,
    'impliedby' : OP_IMPLIED_BY,
    '<-'        : OP_IMPLIED_BY,
    '<=='       : OP_IMPLIED_BY,
    '\u2190'    : OP_IMPLIED_BY,
    '\u2194'    : OP_EQUIVALENT,
    'equivalent': OP_EQUIVALENT,
    '<->'       : OP_EQUIVALENT,
    '<=>'       : OP_EQUIVALENT,
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
        assert (isinstance(op, str) or
                (isinstance(op, numbers.Number) and not args)),\
               '{0}({1})'.format(op, args)
        self.op = num_or_str(op)
        self.args = list(map(to_expr, args)) ## Coerce args to Exprs

    def __str__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        if not self.args:         # Constant or proposition with arity 0
            return str(self.op)
        elif is_symbol(self.op):  # Functional or propositional operator
            return '%s(%s)' % (self.op, ', '.join(map(str, self.args)))
        elif len(self.args) == 1: # Prefix operator
            return self.op + str(self.args[0])
        else:                     # Infix operator
            return '(%s)' % (' '+self.op+' ').join(map(str, self.args))

    def __repr__(self):
        "Show something like 'P' or '(P x, y)', or '(~ P)' or '(| P Q R)'"
        if not self.args:         # Constant or proposition with arity 0
            return str(self.op)
        else :
            return '(%s %s)' % (self.op, ', '.join(map(repr, self.args)))

    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return (other is self) or (isinstance(other, Expr)
            and self.op == other.op and self.args == other.args)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.args))

    def numops(self):
        """ Return the number of operators in an expression. """
        if len(self.args) == 0: return 0
        return 1 + sum(map(lambda x: x.numops(), self.args))

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
        if isinstance(vars, Expr):
            self.vars = [vars]
        else:
            self.vars = list(map(to_expr, vars))

    def __repr__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        return '{0} {1}: ({2})'.format(self.op,
                                ', '.join(map(repr, self.vars)),
                                ', '.join(map(repr, self.args)))

    def __str__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        return '{0} {1}: ({2})'.format(self.op,
                                ', '.join(map(str, self.vars)),
                                ', '.join(map(str, self.args)))
    
    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return (isinstance(other, Quantifier) and
                self.op == other.op and
                self.vars == other.vars and
                self.args == other.args)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.vars)) ^ hash(tuple(self.args))


def opposite(quant):
    """ Return opposite quantifier (forall -> exists; exists -> forall) """
    if quant == OP_EXISTS:
        return OP_FORALL
    if quant == OP_FORALL:
        return OP_EXISTS
    assert False, 'Unknown quantifier "{0}"'.format(quant)


def is_symbol(s):
    "A string s is a symbol if it starts with an alphabetic char."
    return ((isinstance(s, str) and
             (s[0].isalpha() or s[0] == '?') and
             (s != OP_FORALL and s != OP_EXISTS)) or
             isinstance(s, numbers.Number))


def is_var_symbol(s):
    "A logic variable symbol is an initial-lowercase string."
    try:
        return is_symbol(s) and (s[0] == '?' or s[0].islower())
    except:
        return False


def is_function_symbol(s):
    "A string s is a symbol if it starts with an initial-lowercase string."
    try:
        return is_symbol(s) and s[0].islower()
    except:
        return False


def is_prop_symbol(s):
    """A proposition logic symbol is an initial-uppercase string other than
    TRUE or FALSE."""
    try:
        return is_symbol(s) and s[0].isupper() and s != 'TRUE' and s != 'FALSE'
    except:
        return False


def is_variable(f):
    """Formula f is a variable if it has a variable symbol as an operator. """
    return is_var_symbol(f.op)


def is_constant(f):
    """Formula f is a constant if its op is a function symbol with no args. """
    return ((is_function_symbol(f.op) and len(f.args) == 0) or
            (isinstance(f.op, numbers.Number)))


def is_function(f):
    """Formula f is a function if its op is a function symbol with args. """
    return (is_function_symbol(f.op) and len(f.args) > 0)


def is_term(f):
    """Formula f is a term if it is a variable, constant or a function. """
    return (is_variable(f) or is_constant(f) or is_function(f))


def is_predicate(f):
    """Formula f is a predicate if it start with an upper case letter. """
    return is_prop_symbol(f.op)


def is_quantified(f):
    """Formula f is quantifie if the operator is a quantifier. """
    return (f.op == OP_EXISTS or f.op == OP_FORALL)


def is_atomic_formula(f):
    """Formula f is an atomic formula if it is =, != or a predicate. """
    return (f.op == OP_EQUALS or f.op == OP_NOTEQUALS or is_prop_symbol(f.op))


def is_true(f):
    """ Return True if the operator is OP_TRUE (ignore case). """
    return str(f.op).upper() == OP_TRUE


def is_false(f):
    """ Return True if the operator is OP_FALSE (ignore case). """
    return str(f.op).upper() == OP_FALSE


def vars(s):
    """ Return all variables in a formula (including vars in quantifiers). """
    if is_variable(s):
        return {s}
    elif is_quantified(s):
        return set(s.vars).union(*list(map(vars, s.args)))
    else:
        return set().union(*list(map(vars, s.args)))


def fvars(s):
    """ Return free variables. """
    if is_variable(s):
        return {s}
    elif is_quantified(s):
        return set().union(*list(map(fvars, s.args))) - set(s.vars)
    else:
        return set().union(*list(map(fvars, s.args)))


def generalise(f):
    """Take a formula and bind all free variables to a universal quantifier. """
    return Quantifier(OP_FORALL, fvars(f), f)


def variant(x, vars):
    """ Create a variant of a variable name. If the variable x appears 
    in the set of variables, add an apostrophe and try again.
    
    >>> variant('x', ['y', 'z'])
    "x"
    >>> variant('x', ['x', 'y', 'z'])
    "x'"
    
    """
    if x in vars: return variant(Expr(x.op + "'", *x.args), vars)
    else: return x


def subst(mappings, tm):
    """ Substitute terms in a formula.
    
    For example, to substitute 'c' by 'x' the variable in forall x has to be
    renamed to something else (x' in our case).
    
    >>> subst({Expr('c'): Expr('x')}, expr('forall x: c > 0 -> x + c > x'))
    #   --> "forall x': x > 0 -> x' + x > x'"
    
    """
    if is_variable(tm):
        if tm in mappings: return mappings[tm]
        else: return tm
    if is_quantified(tm):
        for var in tm.vars:
            # get the list of existing variables in the mappings
            existing_vars = set().union(*list(map(vars, mappings.values())))
            # rename any quantifier variable that would become bound by subst.
            if var in existing_vars:
                var2 = variant(var, existing_vars)
                mappings[var] = var2
        return Quantifier(tm.op,
                          [subst(mappings, x) for x in tm.vars],
                          *[subst(mappings, x) for x in tm.args])
    else:
        return Expr(tm.op, *[subst(mappings, x) for x in tm.args])


def deepen(f):
    """ Return a copy of f where each operator takes at most 2 arguments.
    >>> flatten(expr('A & B & C')) == expr('A & (B & C))
    True
    
    """
    if is_quantified(f):
        if len(f.vars) > 1:
            return Quantifier(f.op, f.vars[0],
                              deepen(Quantifier(f.op, f.vars[1:], f.args[0])))
        else:
            return Quantifier(f.op, f.vars, deepen(f.args[0]))
    elif f.op == OP_AND or f.op == OP_OR:
        args = [deepen(x) for x in f.args]
        if len(args) == 1:
            return args[0]
        elif len(args) > 2:
            return Expr(f.op, args[0], deepen(Expr(f.op, *args[1:])))
        else:
            return Expr(f.op, *args)
    elif f.op in [OP_IMPLIES, OP_IMPLIED_BY, OP_EQUIVALENT]:
        return Expr(f.op, *[deepen(x) for x in f.args])
    elif f.op == OP_NOT:
        return Expr(f.op, deepen(f.args[0]))
    else:
        return f


def flatten(f):
    """ Return a copy of f where each operator takes as many arguments
    as possible.
    >>> flatten(expr('A & (B & C)')) == expr('A & B & C)
    True
    
    """
#    print('flatten({0})'.format(str(f)))
    if is_quantified(f):
        arg = flatten(f.args[0])
        if is_quantified(arg) and f.op == arg.op:
            return Quantifier(f.op, f.vars + arg.vars, arg.args[0])
        else:
            return Quantifier(f.op, f.vars, arg)
    elif f.op == OP_AND or f.op == OP_OR:
        args = list(map(flatten, f.args))
        same_args = list(filter(lambda x: x.op == f.op, args))
        new_args = []
        for el in same_args:
            new_args.extend(el.args)
        other_args = [x for x in args if x not in same_args]
        return Expr(f.op, *(other_args + new_args))
    elif f.op in [OP_IMPLIES, OP_IMPLIED_BY, OP_EQUIVALENT]:
        return Expr(f.op, *[flatten(x) for x in f.args])
    elif f.op == OP_NOT:
        return Expr(f.op, flatten(f.args[0]))
    else:
        return f


def simplify(f):
    """ Take a FOL formula and try to simplify it. """
#    print('\nSimplifying op "{0}" args "{1}"'.format(f.op, f.args))
    if is_quantified(f): # remove variable that are not in f
        vars = set(f.vars)
        fv = fvars(f.args[0])
        needed = vars & fv
        if needed == set():
            return simplify(f.args[0])
        else:
            arg = simplify(f.args[0])
            variables = [v for v in f.vars if v in needed] # keep the same order
            if (arg != f.args[0]) or (len(needed) < len(f.vars)):
                return simplify(Quantifier(f.op, variables, arg))
            else:
                return f
    elif f.op == OP_NOT:
        arg = f.args[0]
        if arg.op == OP_NOT: # double neg
            return simplify(arg.args[0])
        elif is_true(arg): # -TRUE --> FALSE
            return Expr(OP_FALSE)
        elif is_false(arg): # -FALSE --> TRUE
            return Expr(OP_TRUE)
        elif arg.op == OP_EQUALS:
            return Expr(OP_NOTEQUALS,
                        simplify(arg.args[0]),
                        simplify(arg.args[1]))
        elif arg.op == OP_NOTEQUALS:
            return Expr(OP_EQUALS,
                        simplify(arg.args[0]),
                        simplify(arg.args[1]))
        else:
            arg2 = simplify(arg)
            if arg2 != arg:
                return simplify(Expr(OP_NOT, arg2))
            return f
    elif f.op == OP_AND:
        if any(map(is_false, f.args)): # if one conjuct is FALSE, expr is FALSE
            return Expr(OP_FALSE)
        elif len(f.args) == 1:
            return simplify(f.args[0])
        else: # remove conjuncts that are TRUE and simplify args
            args = list(map(simplify, filter(lambda x: not is_true(x),f.args)))
            # FIXME: remove arguments that appear multiple times in AND and OR
            used = set()
            if args != f.args:
                unique = []
                for arg in args:
                    if arg not in used:
                        used.add(arg)
                        unique.append(arg)
                return simplify(Expr(OP_AND, *unique))
            else:
                return f
    elif f.op == OP_OR:
        if any(map(is_true, f.args)): # if one conjuct is TRUE, expr is TRUE
            return Expr(OP_TRUE)
        elif len(f.args) == 1:
            return simplify(f.args[0])
        else: # remove conjuncts that are TRUE and simplify args
            args = list(map(simplify, filter(lambda x: not is_false(x),f.args)))
            if args != f.args:
                return simplify(Expr(OP_OR, *args))
            else:
                return f
    elif f.op == OP_IMPLIES:
        if is_false(f.args[0]) or is_true(f.args[1]):
            return Expr(OP_TRUE)
        elif is_true(f.args[0]):
            return simplify(f.args[1])
        elif is_false(f.args[1]):
            return simplify(Expr(OP_NOT, simplify(f.args[0])))
        else:
            arg1 = simplify(f.args[0])
            arg2 = simplify(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return simplify(Expr(OP_IMPLIES, arg1, arg2))
            else:
                return f
    elif f.op == OP_IMPLIED_BY:
        if is_false(f.args[1]) or is_true(f.args[0]):
            return Expr(OP_TRUE)
        elif is_true(f.args[1]):
            return simplify(f.args[0])
        elif is_false(f.args[0]):
            return simplify(Expr(OP_NOT, simplify(f.args[1])))
        else:
            arg1 = simplify(f.args[0])
            arg2 = simplify(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return simplify(Expr(OP_IMPLIES, arg1, arg2))
            else:
                return f
    elif f.op == OP_EQUIVALENT:
        if is_true(f.args[0]):
            return simplify(f.args[1])
        elif is_true(f.args[1]):
            return simplify(f.args[0])
        elif is_false(f.args[0]):
            return simplify(Expr(OP_NOT, simplify(f.args[1])))
        elif is_false(f.args[1]):
            return simplify(Expr(OP_NOT, simplify(f.args[0])))
        else:
            arg1 = simplify(f.args[0])
            arg2 = simplify(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return simplify(Expr(OP_EQUIVALENT, arg1, arg2))
            else:
                return f
    else:
        return f


def remove_conditionals(f):
    """ Return a copy of f where conditionals are replaced by & and |. """
    if f.op == OP_IMPLIES:
        p, q = f.args[0], f.args[1]
        return (remove_conditionals(~p) | remove_conditionals(q))
    elif f.op == OP_IMPLIED_BY:
        p, q = f.args[0], f.args[1]
        return (remove_conditionals(p) | remove_conditionals(~q))
    elif f.op == OP_EQUIVALENT:
        p, q = f.args[0], f.args[1]
        return (remove_conditionals(p) & remove_conditionals(q) |
                remove_conditionals(~p) & remove_conditionals(~q))
    elif is_quantified(f):
        return Quantifier(f.op, f.vars, remove_conditionals(f.args[0]))
    else:
        return Expr(f.op, *[remove_conditionals(x) for x in f.args])


def push_neg(f):
    """ Return a copy of f that has negation as close to terms as possible. 
    Unlike nnf(), push_neg() leaves conditionals as they are.
    
    """
    if f.op == OP_NOT:
        arg = f.args[0]
        if arg.op == OP_NOT:
            return push_neg(arg.args[0])
        elif arg.op == OP_AND:
            return Expr(OP_OR, *[push_neg(Expr(OP_NOT, x)) for x in arg.args])
        elif arg.op == OP_OR:
            return Expr(OP_AND, *[push_neg(Expr(OP_NOT, x)) for x in arg.args])
        elif arg.op == OP_IMPLIES: # p -> q
            p, q = arg.args[0], arg.args[1]
            return ~(push_neg(p) >> push_neg(q))
        elif arg.op == OP_IMPLIED_BY: # p <- q
            p, q = arg.args[0], arg.args[1]
            return ~(push_neg(p) << push_neg(q))
        elif arg.op == OP_EQUIVALENT: # p <-> q
            p, q = arg.args[0], arg.args[1]
            return ~(push_neg(p) ** push_neg(q))
        elif arg.op == OP_FORALL:
            return Quantifier(OP_EXISTS, arg.vars,
                              push_neg(Expr(OP_NOT, arg.args[0])))
        elif arg.op == OP_EXISTS:
            return Quantifier(OP_FORALL, arg.vars,
                              push_neg(Expr(OP_NOT, arg.args[0])))
        else:
            return f
    elif f.op == OP_AND or f.op == OP_OR:
            return Expr(f.op, *[push_neg(x) for x in f.args])
    elif f.op == OP_IMPLIES:
        p, q = f.args[0], f.args[1]
        return (push_neg(p) >> push_neg(q))
    elif f.op == OP_IMPLIED_BY:
        p, q = f.args[0], f.args[1]
        return (push_neg(p) << push_neg(q))
    elif f.op == OP_EQUIVALENT:
        p, q = f.args[0], f.args[1]
        return (push_neg(p) ** push_neg(q))
    elif is_quantified(f):
        return Quantifier(f.op, f.vars, push_neg(f.args[0]))
    else:
        return f
        

def nnf(f):
    """ Create a Negated Normal Form """
    return push_neg(remove_conditionals(simplify(f)))


def unique_vars(f):
    """ Rename variable so that each variable appears only once per formula.
    >>> unique_vars(expr('(forall x: P(x)) | (forall x: Q(x)))')
    expr("(forall x: P(x)) | (forall x': Q(x'))")
    
    """
    def helper(f, used, substs):
        if is_variable(f):
            if f in substs: return substs[f]
            else: return f
        if is_quantified(f):
            # does this quantifier use a variable that is already used?
            clashing = (used & set(f.vars)) # set intersection
            if len(clashing) > 0:
                for var in clashing:
                    existing = used.union(*list(map(vars, substs.values())))
                    # rename any clashing variable
                    var2 = variant(var, existing)
                    substs[var] = var2
                used.update(f.vars)
                arg = helper(f.args[0], used, substs)
                return Quantifier(f.op,
                                  [subst(substs, x) for x in f.vars],
                                  *[subst(substs, x) for x in f.args])
            else:
                used.update(f.vars)
                arg = helper(f.args[0], used, substs)
                return Quantifier(f.op, f.vars, arg)
        else:
            return Expr(f.op, *[helper(x, used, substs) for x in f.args])
    return helper(f, set(), {})


def pull_quants(f):
    """ Pull out quantifiers to the front of the formula f.
    The function assumes that all operators have at most two arguments 
    and all quantifiers have at most one variable 
    (this can be achieved using the function deepen()).
    Also, each variabl name can be used only once per formula.
    
    """
    def rename_and_pull(f, quant, old_var1, old_var2, arg1, arg2):
        """ Helper function that renames given variable in a formula. """
        # when both variables are to be renamed, re-use the variable name
        # eg. (forall x: P(x) & forall y: Q(y)) <-> (forall x: P(x) & Q(x))
        new_var = None
        if old_var1: # rename left?
            new_var = variant(old_var1, fvars(f))
            a1 = subst({old_var1: new_var}, arg1)
        else:
            a1 = arg1
        if old_var2: # rename right?
            if not new_var:
                new_var = variant(old_var2, fvars(f))
            a2 = subst({old_var2: new_var}, arg2)
        else:
            a2 = arg2
        return Quantifier(quant, new_var, pullquants(Expr(f.op, a1 , a2)))

    def pullquants(f):
    #    print('pullquants({0})'.format(str(f)))
        if f.op == OP_AND:
            arg1 = pullquants(f.args[0])
            arg2 = pullquants(f.args[1])
            if arg1.op == OP_FORALL and arg2.op == OP_FORALL:
                return rename_and_pull(f, OP_FORALL,
                                       arg1.vars[0], arg2.vars[0],
                                       arg1.args[0], arg2.args[0])
            elif is_quantified(arg1):
                return rename_and_pull(f, arg1.op,
                                       arg1.vars[0], None,
                                       arg1.args[0], arg2)
            elif is_quantified(arg2):
                return rename_and_pull(f, arg2.op,
                                       None, arg2.vars[0],
                                       arg1, arg2.args[0])
            else:
                return (arg1 & arg2)
        elif f.op == OP_OR:
            arg1 = pullquants(f.args[0])
            arg2 = pullquants(f.args[1])
            if arg1.op == OP_EXISTS and arg2.op == OP_EXISTS:
                return rename_and_pull(f, OP_EXISTS,
                                       arg1.vars[0], arg2.vars[0],
                                       arg1.args[0], arg2.args[0])
            elif is_quantified(arg1):
                return rename_and_pull(f, arg1.op,
                                       arg1.vars[0], None,
                                       arg1.args[0], arg2)
            elif is_quantified(arg2):
                return rename_and_pull(f, arg2.op,
                                       None, arg2.vars[0],
                                       arg1, arg2.args[0])
            else:
                return (arg1 | arg2)
        elif f.op == OP_IMPLIES:
            arg1 = pullquants(f.args[0])
            arg2 = pullquants(f.args[1])
            if is_quantified(arg1):
                return rename_and_pull(f, opposite(arg1.op),
                                       arg1.vars[0], None,
                                       arg1.args[0], arg2)
            elif is_quantified(arg2):
                return rename_and_pull(f, arg2.op,
                                       None, arg2.vars[0],
                                       arg1, arg2.args[0])
            else:
                return (arg1 >> arg2)
        elif f.op == OP_IMPLIED_BY:
            arg1 = pullquants(f.args[0])
            arg2 = pullquants(f.args[1])
            if is_quantified(arg1):
                return rename_and_pull(f, arg1.op,
                                       arg1.vars[0], None,
                                       arg1.args[0], arg2)
            elif is_quantified(arg2):
                return rename_and_pull(f, opposite(arg2.op),
                                       None, arg2.vars[0],
                                       arg1, arg2.args[0])
            else:
                return (arg1 << arg2)
        elif f.op == OP_EQUIVALENT:
            arg1 = pullquants(f.args[0])
            arg2 = pullquants(f.args[1])
            return pullquants((arg1 >> arg2) & (arg1 << arg2))
        elif f.op == OP_NOT:
            arg = pullquants(f.args[0])
            if is_quantified(arg):
                return Quantifier(opposite(arg.op), f.vars, ~(arg.args[0]))
            else:
                return (~arg)
        else:
            return f

    return flatten(pullquants(unique_vars(deepen(f))))


def pnf(f):
    """ Return a copy of formula f in a Prenex Normal Form. """
    return flatten(pull_quants(nnf(f)))


def push_quants(f):
    """Return formula f' equivalent to f in which quantifiers have the smallest
    possible scope. Function assumes that each quantifier has only one variable
    and each operator has at most two arguments. Use deepen() to do that.
    
    """
    def pushquants(f):
    #    print('pushquant({0})'.format(f))
        if is_quantified(f):
            arg = f.args[0]
            if arg.op == OP_NOT:
                return ~pushquants(Quantifier(opposite(f.op), f.vars, arg.args[0]))
            elif is_quantified(arg):
                arg1 = pushquants(arg)
                # did pushquants have any effect?
                if arg1 == arg:
#                    # if no, see if changing the order of the quants has an effect
#                    arg2 = Quantifier(f.op, f.vars, arg.args[0])
#                    arg2_ = pushquants(arg2)
#                    if arg2 == arg2_:
#                        return Quantifier(f.op, f.vars, arg1)
#                    else:
#                        return Quantifier(arg.op, arg.vars, arg2_)
                    return Quantifier(f.op, f.vars, arg1)
                else:
                    return pushquants(Quantifier(f.op, f.vars, arg1))
            elif arg.op in [OP_AND, OP_OR]:
                arg1 = arg.args[0]
                arg2 = arg.args[1]
                variable = f.vars[0]
                if variable in fvars(arg1) and variable in fvars(arg2):
                    if ((arg.op == OP_AND and f.op == OP_FORALL) or
                        (arg.op == OP_OR and f.op == OP_EXISTS)):
                        return pushquants(Expr(arg.op,
                                          Quantifier(f.op, f.vars, arg1),
                                          Quantifier(f.op, f.vars, arg2)))
                    else:
                        return Quantifier(f.op, f.vars, pushquants(arg))
                if variable in fvars(arg1):
                    return pushquants(Expr(arg.op,
                                      Quantifier(f.op, f.vars, arg1), arg2))
                if variable in fvars(arg2):
                    return pushquants(Expr(arg.op, arg1,
                                           Quantifier(f.op, f.vars, arg2)))
                else:
                    get_log().warning('Dropped quantifier "{0} : {1}" from "{2}"'
                                      .format(f.op, f.vars, f))
                    return arg
            elif arg.op == OP_IMPLIES:
                arg1 = arg.args[0]
                arg2 = arg.args[1]
                variable = f.vars[0]
                if variable in fvars(arg1) and variable in fvars(arg2):
                    return Quantifier(f.op, f.vars, pushquants(arg))
                elif variable in fvars(arg1):
                    quant = opposite(f.op)
                    return (pushquants(Quantifier(quant, variable, arg1)) >>
                            pushquants(arg2))
                elif variable in fvars(arg2):
                    return (pushquants(arg1) >>
                            pushquants(Quantifier(f.op, variable, arg2)))
                else:
                    get_log().warning('Dropped quantifier "{0} : {1}" from "{2}"'
                                      .format(f.op, f.vars, f))
                    return (pushquants(arg1) >> pushquants(arg2))
            elif arg.op == OP_IMPLIED_BY:
                arg1 = arg.args[0]
                arg2 = arg.args[1]
                variable = f.vars[0]
                if variable in fvars(arg1) and variable in fvars(arg2):
                    return Quantifier(f.op, f.vars, pushquants(arg))
                elif variable in fvars(arg1):
                    return (pushquants(Quantifier(f.op, variable, arg1)) <<
                            pushquants(arg2))
                elif variable in fvars(arg2):
                    quant = opposite(f.op)
                    return (pushquants(arg1) <<
                            pushquants(Quantifier(quant, variable, arg2)))
                else:
                    get_log().warning('Dropped quantifier "{0} : {1}" from "{2}"'
                                      .format(f.op, f.vars, f))
                    return (pushquants(arg1) << pushquants(arg2))
            else:
                return Quantifier(f.op, f.vars[0], pushquants(f.args[0]))
        elif f.op == OP_NOT:
            return ~pushquants(f.args[0])
        elif f.op in BINARY_LOGIC_OPS:
            return Expr(f.op, *[pushquants(x) for x in f.args])
        else:
            return f

    return pushquants(deepen(f))


def miniscope(f):
    """ Return a normalised copy of f with the minimu scope of quantifiers. """
    return flatten(push_quants(nnf(f)))


def generate_subformulas(f):
    """ Create a generator that returns variants of the formula. 
    >>> list(generate_subformulas(Expr('P') & Expr('Q')))
    [Expr('P'), Expr('Q'), Expr('P) & Expr('Q')]
    
    """
    def subformulas(f):
        if is_quantified(f):
            for fm in subformulas(f.args[0]):
                yield Quantifier(f.op, f.vars, fm)
        elif f.op == OP_NOT:
            for fm in subformulas(f.args[0]):
                yield ~fm
        elif f.op in BINARY_OPS:
            lhs = subformulas(f.args[0])
            for fm in lhs:
                yield fm
            rhs = subformulas(f.args[1])
            for fm in rhs:
                yield fm
            lhs = subformulas(f.args[0])
            for fm1 in lhs:
                rhs = subformulas(f.args[1])
                for fm2 in rhs:
                    yield Expr(f.op, fm1, fm2)
        else:
            yield f
    return subformulas(deepen(f))


def to_prover_str(f):
    """ Return a string representation of f that can be parsed by Prover9. """
    def to_prover(f):
        """ Function assumes each op has at most two args. """
        if f.op == OP_NOT:
            return ('-({arg})'.format(arg=to_prover(f.args[0])))
        elif f.op == OP_AND:
            return ('({arg1} & {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_OR:
            return ('({arg1} | {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_IMPLIES:
            return ('({arg1} -> {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_IMPLIED_BY:
            return ('({arg2} -> {arg1})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_EQUIVALENT:
            return ('({arg1} <-> {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_EQUALS:
            return ('({arg1} = {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_NOTEQUALS:
            return ('({arg1} != {arg2})'
                    .format(arg1=to_prover(f.args[0]),
                            arg2=to_prover(f.args[1])))
        elif f.op == OP_FORALL:
            return ('all {var} ({arg})'
                    .format(var=to_prover(f.vars[0]),
                            arg=to_prover(f.args[0])))
        elif f.op == OP_EXISTS:
            return ('exists {var} ({arg})'
                    .format(var=to_prover(f.vars[0]),
                            arg=to_prover(f.args[0])))
        else:
            return str(f)
    # first make sure each op has at most two args and then use the helper.
    return '{0} .'.format(to_prover(deepen(f)))


# #############################  PARSING  ################################### #


PARSE_DEBUG = False


def get_op(x):
    """ Return a standard operator given an alternative one. """
    if x in OPS: return OPS[x]
    return x


def to_expr(item):
    """ Convert to instance of Expr. """
#    get_log().debug('to_expr: ' + str((repr(type(item)), repr(item))))
    if isinstance(item, str): return Expr(num_or_str(item))
    if isinstance(item, Expr): return item
    if hasattr(item, '__getitem__'): return list(map(to_expr, item))
    return item.to_expr()


class FOLQuant:
    def __init__(self, t):
        tmp = t[0].asDict()
        self.op = get_op(tmp['quantifier'])
        self.vars = tmp['vars'].asList()
        self.args = [tmp['args']]
        if PARSE_DEBUG:
            print('created quant "{0}"'.format(self.op))
            print('\targs "{0}"'.format(self.args))

    def __str__(self):
        vars = ', '.join(self.vars)
        return("%s %s: (" % (self.op, vars)) + ''.join(map(str,self.args)) + ")"

    __repr__ = __str__

    def to_expr(self):
        return Quantifier(self.op, [to_expr(v) for v in self.vars], *self.args)


class FOLBinOp:
    def __init__(self,t):
        self.op = get_op(t[0][1])
        self.args = t[0][0::2]
        if PARSE_DEBUG:
            print('created binop "{0}"'.format(self.op))
            print('\targs "{0}"'.format(self.args))
        
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
        if PARSE_DEBUG:
            print('created unop "{0}"'.format(self.op))
            print('\targs "{0}"'.format(self.args))
        
    def __str__(self):
        return (str(self.op) + "(" + str(self.args) + ")")

    __repr__ = __str__

    def to_expr(self):
        return Expr(self.op, self.args)


class FOLPred:
    def __init__(self,t):
        self.op = get_op(t[0][0])
        self.args = t[0][1]
        if PARSE_DEBUG:
            print('created pred "{0}"'.format(self.op))
            print('\targs "{0}"'.format(self.args))
        
    def __str__(self):
        return (str(self.op) + "(" + ', '.join(map(str,self.args)) + ")")

    __repr__ = __str__

    def to_expr(self):
        return Expr(self.op, *self.args)


# code nicked from the book Programming in Python 3 (kindle)
# optimisation -- before creating any parsing elements
ParserElement.enablePackrat()

# allow python style comments
comment = (Literal('#') + restOfLine).suppress()

LP, RP , colon = map(Suppress, '():')
forall = Keyword('forall') | Literal('\u2200')
exists = Keyword('exists') | Literal('\u2203')
implies = Keyword('==>') | Keyword('implies') | Literal('\u2192') | Literal('->')
implied = Keyword('<==') | Keyword('impliedby') | Literal('\u2190') | Literal('<-')
iff = Keyword('<=>')  | Keyword('iff') | Literal('\u2194') | Keyword('<->')
or_  = Keyword('\\/') | Literal('|') | Keyword('or') | Literal('\u2228')
and_ = Keyword('/\\') | Literal('&') | Keyword('and') | Literal('\u2227')
not_ = Literal('~') | Keyword('not') | Literal('\u00AC')
equals = Literal('=') | Keyword('equals')
notequals = Literal('=/=') | Literal('!=') | \
            Keyword('notequals') | Literal('\u2260')
boolean = (CaselessKeyword('FALSE') | CaselessKeyword('TRUE'))

variable = (~(and_ | or_ | not_ | forall | exists | implied | implies | iff) +
            Combine(Optional('?') + Word(alphas, alphanums + "'")))
constant = (~(and_ | or_ | not_ | forall | exists | implied | implies | iff) +
            Word(alphas, alphanums + "'-_"))
number = Combine(Optional(oneOf('+ -')) + Word(nums) +
                 Optional(Literal('.') + Word(nums)))

math_expr = operatorPrecedence(number | variable,
                [(oneOf('+ -'), 1, opAssoc.RIGHT, FOLUnOp),
                 (oneOf('^'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('* /'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('+ -'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('< <= > >= '), 2, opAssoc.LEFT, FOLBinOp)])


term = Forward() # definition of term will involve itself
terms = delimitedList(term)
predicate = Group(constant + Group(LP + terms + RP)).setParseAction(FOLPred)

term << operatorPrecedence(number | predicate | variable,
                [(oneOf('+ -'), 1, opAssoc.RIGHT, FOLUnOp),
                 (oneOf('^'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('* /'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('+ -'), 2, opAssoc.LEFT, FOLBinOp),
                 (oneOf('< <= > >= '), 2, opAssoc.LEFT, FOLBinOp)])


# main parser for FOL formula
formula = Forward()
formula.ignore(comment)

forall_expression = Group(forall.setResultsName("quantifier") +
                       delimitedList(variable).setResultsName("vars") + colon +
                       formula.setResultsName("args")
                    ).setParseAction(FOLQuant)
exists_expression = Group(exists.setResultsName("quantifier") +
                      delimitedList(variable).setResultsName("vars") + colon +
                      formula.setResultsName("args")).setParseAction(FOLQuant)

operand = forall_expression | exists_expression | boolean | term

# specify the precedence -- highest precedence first, lowest last
operator_list = [(not_, 1, opAssoc.RIGHT, FOLUnOp)]
#
operator_list += [(equals, 2, opAssoc.RIGHT, FOLBinOp),
                  (notequals, 2, opAssoc.RIGHT, FOLBinOp),
                  (and_, 2, opAssoc.LEFT, FOLBinOp),
                  (or_, 2, opAssoc.LEFT, FOLBinOp),
                  (implies, 2, opAssoc.RIGHT, FOLBinOp),
                  (implied, 2, opAssoc.RIGHT, FOLBinOp),
                  (iff, 2, opAssoc.RIGHT, FOLBinOp)]

formula << operatorPrecedence(operand, operator_list)


# #############################  HELPERS  ################################### #


def num_or_str(x):
    """The argument is a string; convert to a number if possible, or strip it.
    >>> num_or_str('42')
    42
    >>> num_or_str(' 42x ')
    '42x'
    """
    if isinstance(x, numbers.Number):
        return x
    try:
        if '.' in x:
            return float(x)
        else:
            return int(x)
    except ValueError:
        return str(x).strip()


class FormulaParseError(Exception):
    pass


def expr(s):
    """ Parse the string s representing a formula and return it as an Expr. """
    try:
        result = formula.parseString(s, parseAll=True)
        return to_expr(result[0])
    except (ParseException, ParseSyntaxException) as err:
        msg=("Syntax error: {0!r}\n{0.line}\n{1}^".\
             format(err, " " * (err.column)))
        raise FormulaParseError(msg)
    except RuntimeError:
        raise FormulaParseError("Infinite loop in parse.")

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

#############################################################################
##
## Copyright (C) 2014 Roman Kutlak, University of Aberdeen.
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
