import logging
import sys

from nlglib.microplanning import *
from nlglib.realisation import basic


def run():
    r = basic.Realiser()
    clauses = [
        Clause(NP(Male('Roman')), VP('is', 'happy')),
        CC(Clause(NP(Male('Roman')), VP('is', 'programming')),
           Clause(NP(Male('he')), VP('is', 'happy'))),
    ]
    for c in clauses:
        realisation = r.realise(c)
        log.info(realisation)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('coding')
    log.addHandler(logging.StreamHandler(stream=sys.stdout))
    run()
