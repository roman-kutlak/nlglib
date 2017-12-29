"""
This example shows the use of nlglib with multiple simplenlg realisers.

"""

from nlglib.realisation.simplenlg.realisation import Realiser
from nlglib.microplanning import *

realise_en = Realiser(host='roman.kutlak.info', port=40000)
realise_es = Realiser(host='roman.kutlak.info', port=40001)


def main():
    p = Clause("María", "perseguir", "un mono")
    p['TENSE'] = 'PAST'
    # expected = 'María persigue un mono.'
    print(realise_es(p))
    p = Clause(NP("la", "rápida", "corredora"), VP("perseguir"), NP("un", "mono"))
    subject = NP("la", "corredora")
    objekt = NP("un", "mono")
    verb = VP("perseguir")
    subject.premodifiers.append("rápida")
    p.subject = subject
    p.predicate = verb
    p.object = objekt
    # expected = 'La rápida corredora persigue un mono.'
    print(realise_es(p))
    p = Clause(NP('this', 'example'), VP('show', 'how cool simplenlg is'))
    # expected = This example shows how cool simplenlg is.
    print(realise_en(p))


if __name__ == '__main__':
    main()
