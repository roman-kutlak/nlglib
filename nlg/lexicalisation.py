from copy import deepcopy
import re
import sys
import traceback

from nlg.structures import *
from nlg.aggregation import *

DEBUG = False

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

load_truck = Clause(you, VP(put, PlaceHolder(0), PP(into, PlaceHolder(1))))
drive_truck = Clause(you, VP(drive, PlaceHolder(0),
                                     PP(from_, PlaceHolder(1)),
                                     PP(to, PlaceHolder(2))))
unload_truck = Clause(you, VP(unload, PlaceHolder(0),
                                       PP(from_, PlaceHolder(1))))
load_airplane = Clause(you, VP(put, PlaceHolder(0),
                                      PP(into, PlaceHolder(1))))

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
takeOff = Clause(uav, VP(Word('is', 'VERB'), Word('taking off', 'VERB')))
flyToTargetArea = Clause(uav, VP(Word('is', 'VERB'), Word('flying to the target area', 'VERB')))
takePhotos = Clause(uav, VP(Word('is', 'VERB'), Word('taking photos', 'VERB')))
selectLandingSite = Clause(uav, VP(Word('is', 'VERB'), Word('selecting landing site', 'VERB')))
flyToAirfieldA = Clause(uav, VP(Word('is', 'VERB'), Word('flying to airfield A', 'VERB')))
flyToAirfieldB = Clause(uav, VP(Word('is', 'VERB'), Word('flying to airfield B', 'VERB')))
flyToBase = Clause(uav, VP(Word('is', 'VERB'), Word('flying to the base', 'VERB')))
Land = Clause(uav, VP(Word('is', 'VERB'), Word('landing', 'VERB')))
SelectRunway = Clause(uav, VP(Word('is', 'VERB'), 'selecting a runway'))
LandOnLongRunway = Clause(uav, VP(Word('is', 'VERB'), Word('landing', 'VERB'), PP('on', 'a long runway')))
LandOnShortRunway = Clause(uav, VP(Word('is', 'VERB'), Word('landing', 'VERB'), PP('on', 'a short runway')))

# Workflow summary phrase specifications
the_workflow = NP(spec='the', head='workflow')
SummariseNumTasks = Clause(the_workflow,
                        VP('has', PlaceHolder('arg_num_steps'), 'tasks'))
SummariseNumChoices = Clause(the_workflow,
                        VP('has', PlaceHolder('arg_num_choices'), 'choices'))


# KickDetection
Drill = VP('drill')
Trip = VP('perform', 'tripping')
AdjustHSP = VP('adjust', 'HSP')
Monitor = VP('check', 'sensors')
SoftShutIn = VP('perform', 'soft', 'shut-in')
HardShutIn = VP('perform', 'hard', 'shut-in')

RecordData = Message('Elaboration',
                     VP('record', 'data', 'using the kill sheet'),
                     None)#PP('on', 'success', VP('assert', 'well_shut')))

sat = None#PP('on', 'success', VP('assert', 'kick_killed'))

WaitAndWeight = Message('Ellaboration',
    VP('kill', 'the kick', 'using the Wait and Weight method'), sat)
DrillersMethod = Message('Ellaboration',
    VP('kill', 'the kick', 'using the Driller\'s method'), sat)
ReverseCirculation = Message('Ellaboration',
    VP('kill', 'the kick', 'using Reverse Circulation'), sat)
Bullheading = Message('Ellaboration',
    VP('kill', 'the kick', 'using Bullheading'), sat)

ReopenWell = VP('reopen', 'the well')

SealWell = VP('seal', 'the well')
PlugWell = VP('plug', 'the well')

EmergencyTask = NP('emergency taks')
NormalTask = NP('task')

Need_speed = Clause(NP('the well'), VP('has to be shut quickly'))

kick = Clause(NP('a kick'), VP('was detected'))

shallow_depth = Clause(NP('the well'), VP('is in shallow depth'))

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
        self.templates['flyToAirfieldA'] = flyToAirfieldA
        self.templates['flyToAirfieldB'] = flyToAirfieldB
        self.templates['flyToBase'] = flyToBase
        self.templates['Land'] = Land
        self.templates['selectRunway'] = SelectRunway
        self.templates['landOnLongRunway'] = LandOnLongRunway
        self.templates['landOnShortRunway'] = LandOnShortRunway
        # workflow summary
        self.templates['SummariseNumTasks'] = SummariseNumTasks
        self.templates['SummariseNumChoices'] = SummariseNumChoices
        # kick detection
        self.templates['Drill'] = Drill
        self.templates['Trip'] = Trip
        self.templates['AdjustHSP'] = AdjustHSP
        self.templates['Monitor'] = Monitor
        self.templates['SoftShutIn'] = SoftShutIn
        self.templates['HardShutIn'] = HardShutIn
        self.templates['RecordData'] = RecordData
        self.templates['WaitAndWeight'] = WaitAndWeight
        self.templates['DrillersMethod'] = DrillersMethod
        self.templates['ReverseCirculation'] = ReverseCirculation
        self.templates['Bullheading'] = Bullheading
        self.templates['SealWell'] = SealWell
        self.templates['PlugWell'] = PlugWell
        self.templates['ReopenWell'] = ReopenWell

        self.templates['kick'] = kick
        self.templates['Need_speed'] = Need_speed
        self.templates['shallow_depth'] = shallow_depth

        self.templates['EmergencyTask'] = EmergencyTask
        self.templates['NormalTask'] = NormalTask
        # Logistics
        self.templates['Edinburgh'] = Clause(you, VP('drive to', 'Edinburgh'))
        self.templates['Perth'] = Clause(you, VP('drive to', 'Perth'))
        self.templates['Kincardine'] = Clause(you, VP('drive to', 'Kincardine'))
        self.templates['Stirling'] = Clause(you, VP('drive to', 'Stirling'))
        self.templates['Inverness'] = Clause(you, VP('drive to', 'Inverness'))
        self.templates['Aberdeen'] = Clause(you, VP('drive to', 'Aberdeen'))


    def template(self, action):
        if action in self.templates:
            return deepcopy(self.templates[action])
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
        raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)


# TODO: lexicalisation should replace Messages by NLG Elements

def lexicalise_message_spec(msg):
    """ Return Element corresponding to given message specification.
    If the lexicaliser can not find correct lexicalisation, it returns None
    and logs the error.
    
    """
    if DEBUG: print('*** called lexicalise message spec!')
    template = templates.template(msg.name)
    if template is None:
        print('no sentence template for "%s"' % msg.name)
        return String(msg.name)
    # find arguments
    args = template.arguments()
    # if there are any arguments, replace them by values
    for arg in args:
        try:
            if DEBUG: print('Replacing %s in %s. ' % (repr(arg), str(template)))
            if isinstance(arg, PlaceHolder):
                val = msg.value_for(arg.id)
                if DEBUG: print(' val = %s' % repr(val))
                template.replace(arg, val)
            elif isinstance(arg, int):
                print('numeric parameter in "%s"' % repr(arg))
                pass
            else:
                print('unknown parameter in "%s"' % repr(arg))
                pass
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('Lexicalisation - replacing argument failed:\n\t%s' % str(e))
            traceback.print_tb(exc_traceback)
    return template


def lexicalise_message(msg):
    """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
    if DEBUG: print('*** called lexicalise message!')
    if msg is None: return None
    nucleus = lexicalise(msg.nucleus)
    satelites = [lexicalise(x) for x in msg.satelites if x is not None]
    return Message(msg.rst, nucleus, *satelites)


def lexicalise_paragraph(msg):
    """ Return a copy of Paragraph with MsgSpecs replaced by NLG Elements. """
    if DEBUG: print('*** called lexicalise paragraph!')
    if msg is None: return None
    messages = [lexicalise(x) for x in msg.messages if x is not None]
    return Paragraph(*messages)


def lexicalise_section(msg):
    """ Return a copy of a Section with MsgSpecs replaced by NLG Elements. """
    if DEBUG: print('*** called lexicalise section!')
    if msg is None: return None
    title = lexicalise(msg.title)
    paragraphs = [lexicalise(x) for x in msg.paragraphs if x is not None]
    return Section(title, *paragraphs)


def lexicalise_document(doc):
    """ Return a copy of a Document with MsgSpecs replaced by NLG Elements. """
    if DEBUG: print('*** called lexicalise document!')
    if doc is None: return None
    title = lexicalise(doc.title)
    sections = [lexicalise(x) for x in doc.sections if x is not None]
    return Document(title, *sections)


# TODO: hwo to lexicalise this given that NLG does know about tasks?
def lexicalise_task(task, document):
    """ Convert a task to a syntax tree with lexical items in it. """
    if DEBUG: print('Lexicalising task %s' % str(task))
    params = task.input_params[:]
    key = task.name
    sent = templates.template(key)
    if None is sent:
        sent = templates.template(task.id)
    if None != sent:
        _replace_placeholders_with_params(sent, params)
    else:
        print('Key "%s" or id "%s" not found' % (task.name, task.id))
    return sent


def _replace_placeholders_with_params(template, params):
    if DEBUG: print('Replacing params in template:\n%s' % str(template))
    if DEBUG: print('Params: \n\t %s' % str(params))
    for c in sentence_iterator(template):
        if (isinstance(c, PlaceHolder)):
            id = c.id
            var = params[id]
            c.object = var
#           print('Replacing parameter %d with %s' % (id, var))






