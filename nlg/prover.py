import os
import logging
import subprocess

from nlg.fol import to_prover_str

def get_log():
    return logging.getLogger(__name__)


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
    try:
        out = subprocess.check_output('../prover9',
                  input=theorem_str,
                  universal_newlines=True,
                  stderr=subprocess.STDOUT)
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
