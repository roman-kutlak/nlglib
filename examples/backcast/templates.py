"""This module provides templates for lexicalisation"""

from nlglib.features import NEGATED
from nlglib.microplanning import *

templates = {
    'no-data': Clause('there', VP('be', NP('no', 'data'), PP('for', Var('date')))),
    'do-not-understand': Clause('I', VP('understand', NP('the', 'goal'), Var('goal'), features=[NEGATED.true])),
}
