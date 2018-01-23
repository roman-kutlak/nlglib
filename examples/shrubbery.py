import logging
import sys

from nlglib.microplanning import *
from nlglib.realisation import basic, simplenlg


def run():
    r = basic.Realiser()
    clauses = [
        Clause(NP(Male('Arthur')), VP('is', NP('a', 'knight'))),
        Clause('you', 'must return', PP('here', PP('with', NP('a', 'shrubbery'))),
               features={'complementiser': 'that'}),
        Clause('you', VP('pass', PP('through', NP('this', 'wood', complements=[Adjective('alive')]))),
               features={'TENSE': 'future', 'complementiser': 'or'}, premodifiers=['never']),
    ]
    for c in clauses:
        realisation = r.realise(c)
        log.info(realisation)
    expected = "HEAD KNIGHT says that you must return here with a shrubbery " \
               "or you will never pass through this wood alive."
    c2 = clauses[1]
    c3 = clauses[2]
    c2.complements += c3
    c = Clause('HEAD KNIGHT', 'say', c2)
    cool_realiser = simplenlg.Realiser(host='nlg.kutlak.info')
    realisation = cool_realiser(c)
    log.info(realisation)
    assert realisation == expected, 'Is simplenlg running?'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('coding')
    log.addHandler(logging.StreamHandler(stream=sys.stdout))
    run()
