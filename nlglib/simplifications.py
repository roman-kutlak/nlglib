import re
import logging
from collections import defaultdict

from nlg import prover
from nlg.fol import flatten, var_for_idx
from nlg.fol import Expr, Quantifier, fvars, opposite, subst, variant, deepen
from nlg.fol import is_predicate, is_quantified, is_true, is_false, is_variable
from nlg.fol import OP_TRUE, OP_FALSE, OP_NOT, OP_AND, OP_OR
from nlg.fol import OP_EQUIVALENT, OP_IMPLIES, OP_IMPLIED_BY
from nlg.fol import OP_EQUALS, OP_NOTEQUALS, OP_FORALL, OP_EXISTS
from nlg.fol import LOGIC_OPS, BINARY_LOGIC_OPS
from nlg.qm import qm

def get_log():
    return logging.getLogger(__name__)

if __name__ == '__main__':
    import logging.config
    logging.basicConfig(level=logging.DEBUG)

def kleene(f):
    """ Take a FOL formula and try to simplify it. """
#    print('\nSimplifying op "{0}" args "{1}"'.format(f.op, f.args))
    if is_quantified(f): # remove variable that are not in f
        vars = set(f.vars)
        fv = fvars(f.args[0])
        needed = vars & fv
        if needed == set():
            return kleene(f.args[0])
        else:
            arg = kleene(f.args[0])
            variables = [v for v in f.vars if v in needed] # keep the same order
            if (arg != f.args[0]) or (len(needed) < len(f.vars)):
                return kleene(Quantifier(f.op, variables, arg))
            else:
                return f
    elif f.op == OP_NOT:
        arg = f.args[0]
        if arg.op == OP_NOT: # double neg
            return kleene(arg.args[0])
        elif is_true(arg): # -TRUE --> FALSE
            return Expr(OP_FALSE)
        elif is_false(arg): # -FALSE --> TRUE
            return Expr(OP_TRUE)
        elif arg.op == OP_EQUALS:
            return Expr(OP_NOTEQUALS,
                        kleene(arg.args[0]),
                        kleene(arg.args[1]))
        elif arg.op == OP_NOTEQUALS:
            return Expr(OP_EQUALS,
                        kleene(arg.args[0]),
                        kleene(arg.args[1]))
        else:
            arg2 = kleene(arg)
            if arg2 != arg:
                return kleene(Expr(OP_NOT, arg2))
            return f
    elif f.op == OP_AND:
        if any(map(is_false, f.args)): # if one conjuct is FALSE, expr is FALSE
            return Expr(OP_FALSE)
        elif len(f.args) == 1:
            return kleene(f.args[0])
        else: # remove conjuncts that are TRUE and simplify args
            args = list(map(kleene, filter(lambda x: not is_true(x),f.args)))
            used = set()
            unique = []
            for arg in args:
                if arg not in used:
                    used.add(arg)
                    unique.append(arg)
            if args != unique or f.args != unique:
                return kleene(Expr(OP_AND, *unique))
            else:
                return f
    elif f.op == OP_OR:
        if any(map(is_true, f.args)): # if one conjuct is TRUE, expr is TRUE
            return Expr(OP_TRUE)
        elif len(f.args) == 1:
            return kleene(f.args[0])
        else: # remove conjuncts that are FALSE and simplify args
            args = list(map(kleene, filter(lambda x: not is_false(x),f.args)))
            used = set()
            unique = []
            for arg in args:
                if arg not in used:
                    used.add(arg)
                    unique.append(arg)
            if args != unique or f.args != unique:
                return kleene(Expr(OP_OR, *unique))
            else:
                return f
    elif f.op == OP_IMPLIES:
        if is_false(f.args[0]) or is_true(f.args[1]):
            return Expr(OP_TRUE)
        elif is_true(f.args[0]):
            return kleene(f.args[1])
        elif is_false(f.args[1]):
            return kleene(Expr(OP_NOT, kleene(f.args[0])))
        else:
            arg1 = kleene(f.args[0])
            arg2 = kleene(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return kleene(Expr(OP_IMPLIES, arg1, arg2))
            else:
                return f
    elif f.op == OP_IMPLIED_BY:
        if is_false(f.args[1]) or is_true(f.args[0]):
            return Expr(OP_TRUE)
        elif is_true(f.args[1]):
            return kleene(f.args[0])
        elif is_false(f.args[0]):
            return kleene(Expr(OP_NOT, kleene(f.args[1])))
        else:
            arg1 = kleene(f.args[0])
            arg2 = kleene(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return kleene(Expr(OP_IMPLIES, arg1, arg2))
            else:
                return f
    elif f.op == OP_EQUIVALENT:
        if is_true(f.args[0]):
            return kleene(f.args[1])
        elif is_true(f.args[1]):
            return kleene(f.args[0])
        elif is_false(f.args[0]):
            return kleene(Expr(OP_NOT, kleene(f.args[1])))
        elif is_false(f.args[1]):
            return kleene(Expr(OP_NOT, kleene(f.args[0])))
        else:
            arg1 = kleene(f.args[0])
            arg2 = kleene(f.args[1])
            if arg1 != f.args[0] or arg2 != f.args[1]:
                return kleene(Expr(OP_EQUIVALENT, arg1, arg2))
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
    return push_neg(remove_conditionals(kleene(f)))


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


def drop_quant(f):
    """Remove quantifiers from a formula. """
    def drop(f):
        if is_quantified(f):
            return drop(f.args[0])
        else:
            return f
    return drop(pull_quants(f))


class EvaluationError(Exception):
    pass


def evaluate_prop(f, assignment):
    """Evaluate a propositional formula with respect to the given assignment.
#    The assignment should be a dict with 2 keys: 'True' and 'False'. The values
#    for those keys should be a collection of strings corresponding to 
#    the operator names - predicates with 0 arity (acting as propositions).
    The assignment maps propositions (0-ary predicates) to True or False.

    """
    if f.op == OP_TRUE:
        return True
    elif f.op == OP_FALSE:
        return False
    elif f.op == OP_NOT:
        return not evaluate_prop(f.args[0], assignment)
    elif f.op == OP_AND:
        return all(evaluate_prop(x, assignment) == True for x in f.args)
    elif f.op == OP_OR:
        return any(evaluate_prop(x, assignment) == True for x in f.args)
    elif f.op == OP_IMPLIES:
        args = [evaluate_prop(x, assignment) for x in f.args]
        return not (args[0] == True and args[1] == False)
    elif f.op == OP_IMPLIED_BY:
        args = [evaluate_prop(x, assignment) for x in f.args]
        return not (args[0] == False and args[1] == True)
    elif f.op == OP_EQUIVALENT:
        args = [evaluate_prop(x, assignment) for x in f.args]
        return (args[0] == args[1])
    elif is_predicate(f) and len(f.args) == 0:
        try:
            return assignment[f]
        except KeyError:
            raise EvaluationError('Predicate "{0}" is not in the assignment.'.
                                  format(str(f)))
    else:
        msg = ('The Quine-McCluskey algorithm is defined only for '
               'propositional logic. The operator "{0}" is not defined '
               'in propositional logic.'.format(f))
        raise EvaluationError(msg)


def collect_propositions(f):
    """Collect propositions (zero-place predicates)."""
    def helper(f, result):
        if is_predicate(f) and len(f.args) == 0:
            result.add(f)
        else:
            for x in f.args:
                helper(x, result)
        return result
    return sorted(helper(f, set()))


def mk_assignment(val, propositions):
    """Assign True or False to `vars` depending on value.
    The value is an integer representing binary values of the vars.
    E.g., 5 would result in the assignment .., 0, 0, 1, 0, 1.

    """
    result = {}
    mask = 1
    vars = list(reversed(propositions))
    for i in range(len(vars)):
        result[vars[i]] = (mask & (val >> i)) == 1
    return result


def calculate_output(f):
    """Calculate the output of the given propositional formula.
    Return 3 lists of numbers corresponsing to when a formula evaluates to
    True, False and don't cate based on alphabetically sorted predicates. 
    
    """
    propositions = collect_propositions(f)
    num_props = len(propositions)
    true, false, dc = [], [], []
    for i in range(2**num_props):
        assignment = mk_assignment(i, propositions)
        y = evaluate_prop(f, assignment)
        if y:
            true.append(i)
        elif not y:
            false.append(i)
        else: # this won't happen with `evaluate_prop()`.
            dc.append(i)
    return true, false, dc


def mk_formula_from(ones, vars=None):
    """Return a formula corresponding to the output of QM algorithm.
    >>> mk_formula_from(['X100', '1X11', '10X0'])
    ((B & ~C & ~D) | (A & C & D) | (A & ~B & ~D))
    
    """
    # is it a contradiction?
    if ones == []:
        return Expr(OP_FALSE)
    first = ones[0]
    # is it a tautology?
    if all(x.lower() == 'x' for x in first):
        return Expr(OP_TRUE)
    # for anything else, return the sum of products
    return Expr(OP_OR, *[mk_product(prod, vars) for prod in ones])


def mk_product(string, vars=None):
    """Make a product (OP_AND) from a string of 1, 0 and X chars. """
    num_vars = len(string)
    if vars is not None:
        assert (len(vars) == num_vars)
    else:
        vars = [var_for_idx(i) for i in range(num_vars)]
    args = []
    for i in range(num_vars):
        if string[i] == '1':
            args.append(vars[i])
        elif string[i] == '0':
            args.append(~vars[i])
    return Expr(OP_AND, *args)


def minimise_qm(f):
    """Calculate the output of a predicate logic formula and return a minimal
    form created by the Quine-McCluskey algorithm.
    
    """
    return kleene(mk_formula_from(
        qm(*(calculate_output(f))), collect_propositions(f)))


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
    get_log().debug('running search for shortest formula using ops {}'
                    .format(operators))
    if max == 0:
        max = h.formula_cost(f)
    closed = set()
    atoms = sorted(collect_propositions(f), key=lambda x: str(x))
    queue = atoms[:]
    best = None
    best_cost = max if max > 0 else 1000
    while queue:
        current = queue.pop(0)
        get_log().debug('...current: {}'.format(str(current)))
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


def minimise_search(f, h_file, ops=LOGIC_OPS, max=-1):
    """Return a formula minimised using the breadth first search. """
    if prover.test_tautology(f, []):
        return Expr(OP_TRUE)
    if prover.test_contradiction(f, []):
        return Expr(OP_FALSE)
    h = Heuristic(h_file)
    return bfs(f, h, ops, max)


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
