"""
This example shows the use of nlglib with simplenlg-es.

For this to work, you have to have the simplengl server
of the spanish version running on port 50007

"""
import logging

from nlglib.realisation.simplenlg.realisation import SimplenlgClient, Realiser
from nlglib.microplanning import *

english_client = SimplenlgClient('roman.kutlak.info', 40000)
spanish_client = SimplenlgClient('roman.kutlak.info', 40001)

realise_en = Realiser(client=english_client)
realise_es = Realiser(client=spanish_client)


def main():
    p = Clause("María", "perseguir", "un mono")
    # expected = 'María persigue un mono.'
    p['TENSE'] = 'PAST'
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
    p = Clause(NP('this', 'example'), VP('show', 'how cool is simplenlg'))
    print(realise_en(p))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    main()
