# from nlglib import pipeline
from nlglib.features import tense, aspect
from nlglib.microplanning import *
from nlglib.realisation.simplenlg import Realiser
from nlglib.lexicalisation import Lexicaliser
from nlglib.macroplanning import expr, formula_to_rst

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)

realise = Realiser(host='roman.kutlak.info')
# realise = str


def run_simple_examples():
    s = String('This is my string')
    print(realise(s))

    s = Clause(NNP('John'), VP('be', AdjP('happy')))
    print(realise(s))

    s = Clause(NNP('Paul'), VP('play', NP('guitar'), features={aspect.progressive, }))
    print(realise(s))

    guitarists = Coordination(Clause(NNP('John'),
                                     VP('play', NP('a', 'guitar'),
                                        features={aspect.progressive, tense.past, })),
                              Clause(NNP('George'),
                                     VP('play', NP('a', 'guitar'),
                                        features={aspect.progressive, tense.past, })),
                              Clause(NNP('Paul'),
                                     VP('play', NP('a', 'guitar'),
                                        features={aspect.progressive, tense.past, }))
                              )
    print(realise(guitarists))

    gringo = Coordination(Clause(NNP('George'),
                                 VP('play', NP('a', 'bass'),
                                    features={aspect.progressive, tense.past, })),
                          Clause(NNP('Ringo'),
                                 VP('play', NP('drum', features={number.plural, }),
                                    features={aspect.progressive, tense.past, }))
                          )
    print(realise(gringo))


def run_pipeline():
    templates = {
        'john': NNP(Male('John')),
        'paul': NNP(Male('Paul')),
        'george': NNP(Male('George')),
        'ringo': NNP(Male('Ringo')),
        'guitar': Noun('guitar'),
        'bass': Noun('bass guitar'),
        'drums': Noun('drum', features={number.plural, }),
        'Happy': Clause(NP(Var(0)), VP('be', AdjP('happy'))),
        'Play': Clause(NP(Var(0)), VP('play', NP(Var(1)))),
    }

    lex = Lexicaliser(templates=templates)
    # FIXME: embedded coordination doesn't work
    input_str = 'Play(john, guitar) & Play(paul, guitar) & ' \
                'Play(george, bass) & Play(ringo, drums)'
    sentence = lex(formula_to_rst(expr(input_str)))
    for e in sentence.elements():
        print(repr(e))

    output_str = realise(sentence)
    print(output_str)


if __name__ == '__main__':
    print('starting')
    run_simple_examples()
    print('*' * 80)
    run_pipeline()
    print('done')
