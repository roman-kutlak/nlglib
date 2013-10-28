from copy import deepcopy
import re

from nlg.structures import *
from nlg.aggregation import *

# this should be read from a domain lexicalisation file
fly = Word('fly', 'VERB')
put = Word('load', 'VERB')
move = Word('move', 'VERB')
using = Word('using', 'VERB')
drive = Word('drive', 'VERB')
unload = Word('unload', 'VERB')

into = Word('into', 'PREPOSITION')
from_ = Word('from', 'PREPOSITION')
to = Word('to', 'PREPOSITION')

you = None # Word('you', 'PRONOUN')

load_truck = Clause(you, VP(put, [PlaceHolder(0),
                                  PP(into, PlaceHolder(1))]))
drive_truck = Clause(you, VP(drive, [PlaceHolder(0),
                                     PP(from_, PlaceHolder(1)),
                                     PP(to, PlaceHolder(2))]))
unload_truck = Clause(you, VP(unload, [PlaceHolder(0),
                                       PP(from_, PlaceHolder(1))]))
load_airplane = Clause(you, VP(put, [PlaceHolder(0),
                                      PP(into, PlaceHolder(1))]))

fly_airplane = deepcopy(drive_truck)
fly_airplane.vp.head = fly
unload_airplane = unload_truck

move = Clause(you, VP(move, [PlaceHolder(0),
                             PP(from_, PlaceHolder(1)),
                             PP(to, PlaceHolder(2)),
                             VP(using, PlaceHolder(3))]))
start = Clause(you, VP(Word('start', 'VERB')))
finish = Clause(you, VP(Word('finished', 'VERB')))


# UAV domain

uav = Word('UAV', 'NOUN')
takeOff = Clause(uav, VP(Word('is', 'VERB'), [Word('taking off', 'VERB')]))
flyToTargetArea = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to the target area', 'VERB')]))
takePhotos = Clause(uav, VP(Word('is', 'VERB'), [Word('taking photos', 'VERB')]))
selectLandingSite = Clause(uav, VP(Word('is', 'VERB'), [Word('selecting landing site', 'VERB')]))
flyToLandingSiteA = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to site A', 'VERB')]))
flyToLandingSiteB = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to site B', 'VERB')]))
land = Clause(uav, VP(Word('is', 'VERB'), [Word('landing', 'VERB')]))


class SentenceTemplates:
    """SentenceTemplates provides mapping from STRIPS operators to sentences.
        The keys are actionN where N is the number of parameters. These
        are mapped to string compatible with string.format().
    """

    def __init__(self):
        self.templates = dict()
        self.templates['load-truck'] = load_truck
        self.templates['drive-truck'] = drive_truck
        self.templates['unload-truck'] = unload_truck
        self.templates['load-airplane'] = load_airplane
        self.templates['fly-airplane'] = fly_airplane
        self.templates['unload-airplane'] = unload_airplane
        self.templates['move'] = move
        self.templates['inputCondition'] = start
        self.templates['outputCondition'] = finish
        self.templates['OutputCondition'] = finish
        self.templates['End'] = finish

        self.templates['takeOff'] = takeOff
        self.templates['flyToTargetArea'] = flyToTargetArea
        self.templates['takePhotos'] = takePhotos
        self.templates['selectLandingSite'] = selectLandingSite
        self.templates['flyToLandingSiteA'] = flyToLandingSiteA
        self.templates['flyToLandingSiteB'] = flyToLandingSiteB
        self.templates['land'] = land


    def template(self, action):
        if action in self.templates:
            return self.templates[action]
        else:
            return None


