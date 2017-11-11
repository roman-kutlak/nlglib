"""
This example shows the use of nlglib with simplenlg-es.

For this to work, you have to have the simplengl server
of the spanish version running on port 50007

"""
import logging

from nlglib.realisation.backends.simplenlg.realisation import realise, SimplenlgClient
from nlglib.structures import *
from nlglib.structures.factories import *

english_client = SimplenlgClient('roman.kutlak.info', 40000)
spanish_client = SimplenlgClient('roman.kutlak.info', 40001)


def main():
    p = Clause("María", "perseguir", "un mono")
    # expected = 'María persigue un mono.'
    p['TENSE'] = 'PAST'
    print(realise(p, client=spanish_client))
    p = Clause(NP("la", "rápida", "corredora"), VP("perseguir"), NP("un", "mono"))
    subject = NP("la", "corredora")
    objekt = NP("un", "mono")
    verb = VP("perseguir")
    subject.premodifiers.append("rápida")
    p.subject = subject
    p.predicate = verb
    p.object = objekt
    # expected = 'La rápida corredora persigue un mono.'
    print(realise(p, client=spanish_client))
    p = Clause(NP('this', 'example'), VP('show', 'how cool is simplenlg'))
    print(realise(p, client=english_client))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    main()
