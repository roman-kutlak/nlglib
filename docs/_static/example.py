from nlglib.aggregation import aggregate
from nlglib import pipeline
from nlglib.lexicon import NP, NNP, VP, AdjP, Tense, Aspect, Number, Noun, Gender
from nlglib.realisation.backends.simplenlg import realise
from nlglib.structures import String, Clause, Coordination, Var

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


def run_simple_examples():
    s = String('This is my string')
    print(realise(s))

    s = Clause(NNP('John'), VP('be', AdjP('happy')))
    print(realise(s))

    s = Clause(NNP('Paul'), VP('play', NP('guitar'), features=dict([Aspect.progressive])))
    print(realise(s))

    guitarists = Coordination(Clause(NNP('John'),
                                     VP('play', NP('a', 'guitar'),
                                        features=dict([Aspect.progressive, Tense.past]))),
                              Clause(NNP('George'),
                                     VP('play', NP('a', 'guitar'),
                                        features=dict([Aspect.progressive, Tense.past]))),
                              Clause(NNP('Paul'),
                                     VP('play', NP('a', 'guitar'),
                                        features=dict([Aspect.progressive, Tense.past])))
                              )
    print(realise(guitarists))
    print(realise(aggregate(guitarists)))

    gringo = Coordination(Clause(NNP('George'),
                                 VP('play', NP('a', 'bass'),
                                    features=dict([Aspect.progressive, Tense.past]))),
                          Clause(NNP('Ringo'),
                                 VP('play', NP('drum', features=dict([Number.plural])),
                                    features=dict([Aspect.progressive, Tense.past])))
                          )
    print(realise(gringo))
    print(realise(aggregate(gringo)))


def run_pipeline():
    templates = {
        'john': NNP('John', features=dict([Gender.masculine])),
        'paul': NNP('Paul', features=dict([Gender.masculine])),
        'george': NNP('George', features=dict([Gender.masculine])),
        'ringo': NNP('Ringo', features=dict([Gender.masculine])),
        'guitar': Noun('guitar'),
        'bass': Noun('bass guitar'),
        'drums': Noun('drum', features=dict([Number.plural])),
        'Happy': Clause(NP(Var(0)), VP('be', AdjP('happy'))),
        'Play': Clause(NP(Var(0)), VP('play', NP(Var(1)))),
    }
    input_str = 'Play(john, guitar) & Play(paul, guitar); ' \
                'Play(george, bass); Play(ringo, drums)'
    p = pipeline.Pipeline(__name__)
    output_str = p.process(input_str, templates=templates)
    print(output_str)


if __name__ == '__main__':
    print('starting')
    run_simple_examples()
    print('*' * 80)
    run_pipeline()
    print('done')
