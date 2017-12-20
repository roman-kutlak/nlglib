# from nlglib import pipeline
from nlglib.features import tense, feature, number, gender
from nlglib.structures.factories import NP, NNP, VP, AdjP, Noun, Adjective, Male
from nlglib.realisation.simplenlg import realise
from nlglib.structures import String, Clause, Coordination, Var
from nlglib.lexicalisation import Lexicaliser
from nlglib.macroplanning import expr, formula_to_rst


import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


def run_simple_examples():
    s = String('This is my string')
    print(realise(s))

    s = Clause(NNP('John'), VP('be', AdjP('happy')))
    print(realise(s))

    s = Clause(NNP('Paul'), VP('play', NP('guitar'), features={feature.PROGRESSIVE: True}))
    print(realise(s))

    guitarists = Coordination(Clause(NNP('John'),
                                     VP('play', NP('a', 'guitar'),
                                        features={feature.PROGRESSIVE: True, 'tense': tense.PAST})),
                              Clause(NNP('George'),
                                     VP('play', NP('a', 'guitar'),
                                        features={feature.PROGRESSIVE: True, 'tense': tense.PAST})),
                              Clause(NNP('Paul'),
                                     VP('play', NP('a', 'guitar'),
                                        features={feature.PROGRESSIVE: True, 'tense': tense.PAST}))
                              )
    print(realise(guitarists))

    gringo = Coordination(Clause(NNP('George'),
                                 VP('play', NP('a', 'bass'),
                                    features={feature.PROGRESSIVE: True, 'tense': tense.PAST})),
                          Clause(NNP('Ringo'),
                                 VP('play', NP('drum', features={'number': number.PLURAL}),
                                    features={feature.PROGRESSIVE: True, 'tense': tense.PAST}))
                          )
    print(realise(gringo))


def run_pipeline():
    templates = {
        'john': NNP('John', features={'gender': gender.MASCULINE}),
        'paul': NNP('Paul', features={'gender': gender.MASCULINE}),
        'george': NNP('George', features={'gender': gender.MASCULINE}),
        'ringo': NNP('Ringo', features={'gender': gender.MASCULINE}),
        'guitar': Noun('guitar'),
        'bass': Noun('bass guitar'),
        'drums': Noun('drum', features={'number': number.PLURAL}),
        'Happy': Clause(NP(Var(0)), VP('be', AdjP('happy'))),
        'Play': Clause(NP(Var(0)), VP('play', NP(Var(1)))),
    }

    lex = Lexicaliser(templates=templates)
    input_str = 'Play(john, guitar) & Play(paul, guitar) & ' \
                'Play(george, bass) & Play(ringo, drums)'
    sentence = lex(formula_to_rst(expr(input_str)))
    print(repr(sentence))
    output_str = realise(sentence)
    print(output_str)


if __name__ == '__main__':
    print('starting')
    run_simple_examples()
    print('*' * 80)
    run_pipeline()
    print('done')
