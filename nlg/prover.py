import os
import sys
import logging
import subprocess

from nlg.fol import deepen
from nlg.fol import OP_TRUE, OP_FALSE, OP_NOT, OP_AND, OP_OR
from nlg.fol import OP_EQUIVALENT, OP_IMPLIES, OP_IMPLIED_BY
from nlg.fol import OP_EQUALS, OP_NOTEQUALS, OP_FORALL, OP_EXISTS
from nlg.utils import LogPipe


def get_log():
    return logging.getLogger(__name__)


if getattr(sys, 'frozen', False): # frozen
    mod_path = os.path.dirname(sys.executable)
else: # unfrozen
    mod_path = os.path.dirname(os.path.realpath(__file__))

prover_path = os.path.join(mod_path, 'prover9')


print("Path at terminal when executing this file")
print(os.getcwd() + "\n")

print("This file path, relative to os.getcwd()")
print(__file__ + "\n")

print("This file full path (following symlinks)")
full_path = os.path.realpath(__file__)
print(full_path + "\n")

print("This file directory and name")
path, file = os.path.split(full_path)
print(path + ' --> ' + file + "\n")

print("This file directory only")
print(os.path.dirname(os.path.realpath(__file__)))


prover_tplt = (
"""
formulas(sos).
  {axioms}
end_of_list.
formulas(goals).
  {formula}
end_of_list.
"""
)

class ProverException(Exception):
    pass


def test_equivalent(f1, f2, axioms):
    """Return True if f1 is equivalent to f2, given a set of axioms. """
    get_log().debug('Testing equivalence:\n{0} <=> {1}'.format(f1, f2))
    return run_prover(f1 ** f2, axioms)


def test_tautology(f, axioms):
    """Return True if f is a tautology, given a set of axioms. """
    get_log().debug('Testing tautology:\n{0}'.format(f))
    return run_prover(f, axioms)


def test_contradiction(f, axioms):
    """Return True if f is a contradiction, given a set of axioms. """
    get_log().debug('Testing contradiction:\n{0}'.format(f))
    return run_prover(~f, axioms)


def run_prover(formula, axioms):
    """ Give the formula and the axioms to the theorem prover and return True
    if the theorem was proved. 
    
    """
    get_log().debug('Running theorem prover with formula:\n{0}'.format(formula))
    get_log().debug('Running theorem prover with axioms:\n{0}'.format(axioms))
    axioms_str = '\n'.join(['{0} .'.format(to_prover_str(x)) for x in axioms])
    formula_str = to_prover_str(formula) + ' .'
    theorem_str = prover_tplt.format(axioms=axioms_str,
                                     formula=formula_str)
#    get_log().debug('Formula for prover9:\n{0}'.format(theorem_str))
    with LogPipe(logging.getLogger('nlg.prover.prover').error) as error_log:
        try:
            get_log().warning('Running: {}'.format(prover_path))
            out = subprocess.check_output(prover_path,
                      input=theorem_str,
                      stderr=error_log,
                      universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            if ex.returncode != 1 and ex.returncode != 2:
                get_log().exception('Theorem prover failed to execute.')
                raise ProverException from ex
            else:
    #            get_log().exception(str(ex))
                return False
        except FileNotFoundError as ex:
            get_log().exception('Could not find prover from path "{0}".'
                                .format(os.getcwd()))
            raise ProverException from ex
        return ('THEOREM PROVED' in out)



def to_prover_str(f):
    """ Return a string representation of f that can be parsed by Prover9. """
    def to_prover(f):
        """ Function assumes each op has at most two args. """
        if f.op == OP_TRUE:
            return '(TRUE | -TRUE)' # no constant for true?
        elif f.op == OP_FALSE:
            return '(TRUE & -TRUE)' # no constant for false?
        elif f.op == OP_NOT:
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
    return to_prover(deepen(f))


