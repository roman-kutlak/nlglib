from aggregation import aggregate
from nlglib import pipeline
from nlglib import nlg
from nlglib.lexicon import NP, NNP, VP, AdjP, Tense, Aspect, Number, Noun, Gender
from nlglib.realisation import Realiser
from nlglib.structures import String, Clause, Coordination, PlaceHolder

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


def run_simple_examples():
    realiser = Realiser()
    s = String('This is my string')
    print(realiser.realise(s))

    s = Clause(NNP('John'), VP('be', AdjP('happy')))
    print(realiser.realise(s))

    s = Clause(NNP('Paul'), VP('play', NP('guitar'), features=dict([Aspect.progressive])))
    print(realiser.realise(s))

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
    print(realiser.realise(guitarists))
    print(realiser.realise(aggregate(guitarists)))

    gringo = Coordination(Clause(NNP('George'),
                                 VP('play', NP('a', 'base'),
                                    features=dict([Aspect.progressive, Tense.past]))),
                          Clause(NNP('Ringo'),
                                 VP('play', NP('drum', features=dict([Number.plural])),
                                    features=dict([Aspect.progressive, Tense.past])))
                          )
    print(realiser.realise(gringo))
    print(realiser.realise(aggregate(gringo)))


def run_pipeline():
    templates = {
        'john': NNP('John', features=dict([Gender.feminine])),
        'paul': NNP('Paul', features=dict([Gender.masculine])),
        'george': NNP('George', features=dict([Gender.masculine])),
        'ringo': NNP('Ringo', features=dict([Gender.masculine])),
        'guitar': Noun('guitar'),
        'bass': Noun('bass guitar'),
        'drums': Noun('drum', features=dict([Number.plural])),
        'Happy': Clause(NP(PlaceHolder(0)), VP('be', AdjP('happy'))),
        'Play': Clause(NP(PlaceHolder(0)), VP('play', NP(PlaceHolder(1)))),
    }
    input_str = 'Play(john, guitar) & Play(paul, guitar); Play(george, bass); Play(ringo, drums)'
    output_str = pipeline.translate(input_str, templates, [])
    print(output_str)


if __name__ == '__main__':
    nlg.init_from_settings()
    print('starting')
    # run_simple_examples()
    print('*' * 80)
    run_pipeline()
    print('done')
    nlg.shutdown()
