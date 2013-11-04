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
finish = Clause(you, VP(Word('finish', 'VERB')))


# UAV domain

uav = Word('UAV', 'NOUN')
takeOff = Clause(uav, VP(Word('is', 'VERB'), [Word('taking off', 'VERB')]))
flyToTargetArea = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to the target area', 'VERB')]))
takePhotos = Clause(uav, VP(Word('is', 'VERB'), [Word('taking photos', 'VERB')]))
selectLandingSite = Clause(uav, VP(Word('is', 'VERB'), [Word('selecting landing site', 'VERB')]))
flyToLandingSiteA = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to site A', 'VERB')]))
flyToLandingSiteB = Clause(uav, VP(Word('is', 'VERB'), [Word('flying to site B', 'VERB')]))
land = Clause(uav, VP(Word('is', 'VERB'), [Word('landing', 'VERB')]))


# Workflow summary phrase specifications
the_workflow = NP(spec='the', head='workflow')
SummariseNumSteps = Clause(the_workflow,
                        VP('has', PlaceHolder('arg_num_steps'), 'steps'))
SummariseNumChoices = Clause(the_workflow,
                        VP('has', PlaceHolder('arg_num_choices'), 'choices'))


# KickDetection
DrillAndMonitor = VP('drill', 'and', 'monitor')
Tripping = VP('perform', 'tripping')
Swabbing = VP('perform', 'swabbing')
CheckSensors = VP('check', 'sensors')
KickPrevention = VP('try', 'to prevent', 'possible kick')
KickRecovery = VP('try', 'to recover', 'from an occuring kick')
SealWell = VP('seal', 'the well')
PlugWell = VP('plug', 'the well')

EmergencyTask = NP('emergency taks')
NormalTask = NP('task')


class SentenceTemplates:
    """SentenceTemplates provides mapping from STRIPS operators to sentences.
        The keys are actionN where N is the number of parameters. These
        are mapped to string compatible with string.format().
    """

    def __init__(self):
        self.templates = dict()
        self.templates['inputCondition'] = start
        self.templates['outputCondition'] = finish
        self.templates['Start'] = start
        self.templates['Finish'] = finish
        self.templates['OutputCondition'] = finish
        self.templates['End'] = finish
        # logistics
        self.templates['load-truck'] = load_truck
        self.templates['drive-truck'] = drive_truck
        self.templates['unload-truck'] = unload_truck
        self.templates['load-airplane'] = load_airplane
        self.templates['fly-airplane'] = fly_airplane
        self.templates['unload-airplane'] = unload_airplane
        self.templates['move'] = move
        # UAV
        self.templates['takeOff'] = takeOff
        self.templates['flyToTargetArea'] = flyToTargetArea
        self.templates['takePhotos'] = takePhotos
        self.templates['selectLandingSite'] = selectLandingSite
        self.templates['flyToLandingSiteA'] = flyToLandingSiteA
        self.templates['flyToLandingSiteB'] = flyToLandingSiteB
        self.templates['land'] = land
        # workflow summary
        self.templates['SummariseNumSteps'] = SummariseNumSteps
        self.templates['SummariseNumChoices'] = SummariseNumChoices
        # kick detection
        self.templates['DrillAndMonitor'] = DrillAndMonitor
        self.templates['Tripping'] = Tripping
        self.templates['Swabbing'] = Swabbing
        self.templates['CheckSensors'] = CheckSensors
        self.templates['KickPrevention'] = KickPrevention
        self.templates['KickRecovery'] = KickRecovery
        self.templates['SealWell'] = SealWell
        self.templates['PlugWell'] = PlugWell
        self.templates['EmergencyTask'] = EmergencyTask
        self.templates['NormalTask'] = NormalTask
        

    def template(self, action):
        if action in self.templates:
            return self.templates[action]
        else:
            return None


templates = SentenceTemplates()


def lexicalise(msg):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, str):
        return String(msg)
    elif isinstance(msg, MsgSpec):
        return lexicalise_message_spec(msg)
    elif isinstance(msg, Message):
        return lexicalise_message(msg)
    elif isinstance(msg, Paragraph):
        return lexicalise_paragraph(msg)
    elif isinstance(msg, Section):
        return lexicalise_section(msg)
    elif isinstance(msg, Document):
        return lexicalise_document(msg)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance')


# TODO: lexicalisation should replace Messages by NLG Elements

def lexicalise_message_spec(msg):
    """ Return Element corresponding to given message specification.
    If the lexicaliser can not find correct lexicalisation, it returns None
    and logs the error.
    
    """
    template = templates.template(msg.name)
    if template is None:
        print('no sentence template for "%s"' % msg.name)
        return None
    # find arguments
    args = list(template.arguments())
    if len(args) == 0: return template
    # if there are any arguments, replace them by values
    for arg in args:
        try:
            val = msg.value_for(arg.id)
            template.replace(arg, val)
        except Exception as e:
            print(e)

    return template


def lexicalise_message(msg):
    """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
    if msg is None: return None
    nucleus = lexicalise(msg.nucleus)
    satelites = [lexicalise(x) for x in msg.satelites if x is not None]
    return Message(msg.rst, nucleus, *satelites)


def lexicalise_paragraph(msg):
    """ Return a copy of Paragraph with MsgSpecs replaced by NLG Elements. """
    if msg is None: return None
    messages = [lexicalise(x) for x in msg.messages if x is not None]
    return Paragraph(*messages)


def lexicalise_section(msg):
    """ Return a copy of a Section with MsgSpecs replaced by NLG Elements. """
    if msg is None: return None
    title = lexicalise(msg.title)
    paragraphs = [lexicalise(x) for x in msg.paragraphs if x is not None]
    return Section(title, *paragraphs)


def lexicalise_document(msg):
    """ Return a copy of a Document with MsgSpecs replaced by NLG Elements. """
    if msg is None: return None
    title = lexicalise(msg.title)
    sections = [lexicalise(x) for x in msg.sections if x is not None]
    return Document(title, *sections)











