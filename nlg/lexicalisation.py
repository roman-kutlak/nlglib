#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################


from copy import deepcopy
import re
import sys
import traceback
import logging

from nlg.structures import *
from nlg.aggregation import *

def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())


def lexicalise(msg):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, str):
        return String(msg)
    elif isinstance(msg, Element):
        return msg
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


# each message should correspond to a clause
def lexicalise_message_spec(msg):
    """ Return Element corresponding to given message specification.
    If the lexicaliser can not find correct lexicalisation, it returns None
    and logs the error.
    
    """
    get_log().debug('Lexicalising message specs')
    template = templates.template(msg.name)
    if template is None:
        get_log().warning('No sentence template for "%s"' % msg.name)
        result = String(str(msg))
        result._features = msg._features.copy()
        return result
    if isinstance(template, str):
        return String(template)
    template.set_features(msg._features.copy())
    # find arguments
    args = template.arguments()
    # if there are any arguments, replace them by values
    for arg in args:
        get_log().debug('Replacing %s in %s. ' % (str(arg), str(template)))
        val = msg.value_for(arg.id)
        get_log().debug(' val = %s' % repr(val))
        template.replace(arg, val)
    return template


# TODO: lexicalisation should replace Messages by {NLG Elements} and use
# RST relations to connect the clauses when applicable.
def lexicalise_message(msg):
    """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising message.')
    if msg is None: return None
    if isinstance(msg.nucleus, list):
        nucleus = [lexicalise(x) for x in msg.nucleus if x is not None]
    else:
        nucleus = lexicalise(msg.nucleus)
    satelites = [lexicalise(x) for x in msg.satelites if x is not None]
    # stick each message into a clause
    result = None
    if msg.rst == 'Conjunction' or msg.rst == 'Disjunction':
        result = CC(*satelites, conj=msg.marker)
    elif msg.rst == 'Imply':
        if (len(satelites) != 1):
            get_log().error('expected only one satelite in implication; got '
                            + str(satelites))
        result = Phrase()
        result.set_head(nucleus)
        result.add_complement(*satelites)
        result.add_front_modifier('if')
        result.add_feature('COMPLEMENTISER', 'then')
    elif msg.rst == 'ImpliedBy':
        if (len(satelites) != 1):
            get_log().error('expected only one satelite in implication; got '
                            + str(satelites))
        result = Phrase()
        result.set_head(nucleus)
        result.add_complement(*satelites)
        result.add_feature('COMPLEMENTISER', 'when')
    elif msg.rst == 'Equivalence':
        if (len(satelites) != 1):
            get_log().error('expected only one satelite in equivalence; got '
                            + str(satelites))
        result = Phrase()
        result.set_head(nucleus)
        result.add_complement(*satelites)
        result.add_feature('COMPLEMENTISER', 'is')
    elif msg.rst == 'Inequivalence':
        if (len(satelites) != 1):
            get_log().error('expected only one satelite in equivalence; got '
                            + str(satelites))
        result = Phrase()
        result.set_head(nucleus)
        result.add_complement(*satelites)
        result.add_feature('COMPLEMENTISER', 'is not')
    elif msg.rst == 'Quantifier':
        # quantifiers have multiple nuclei (variables)
        if (len(satelites) != 1):
            get_log().error('expected only one satelite in implication; got '
                            + str(satelites))
        result = Phrase()
        if len(nucleus) == 1:
            np = NP(nucleus[0], String(msg.marker))
        else:
            cc = CC(*nucleus, conj='and')
            np = NP(cc, String(msg.marker))
        if (msg.marker.startswith('there exist')):
            np.add_complement('such that')
        np.add_post_modifier('(')
        result.set_head(np)
        result.add_complement(*satelites)
#        result.add_front_modifier('(')
        result.add_post_modifier(')')
    elif msg.rst == 'Negation':
        result = Phrase()
        np = NP(nucleus, String(msg.marker))
        np.add_pre_modifier('(')
        result.set_head(np)
        result.add_complement(*satelites)
        result.add_post_modifier(')')
    else:
        get_log().debug('RST is: ' + repr(msg.rst))
        result = Message(msg.rst, nucleus, *satelites)
        result.marker = msg.marker
    return result

def lexicalise_paragraph(msg):
    """ Return a copy of Paragraph with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising paragraph.')
    if msg is None: return None
    messages = [lexicalise(x) for x in msg.messages if x is not None]
    return Paragraph(*messages)


def lexicalise_section(msg):
    """ Return a copy of a Section with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising section.')
    if msg is None: return None
    title = lexicalise(msg.title)
    paragraphs = [lexicalise(x) for x in msg.paragraphs if x is not None]
    return Section(title, *paragraphs)


def lexicalise_document(doc):
    """ Return a copy of a Document with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising document.')
    if doc is None: return None
    title = lexicalise(doc.title)
    sections = [lexicalise(x) for x in doc.sections if x is not None]
    return Document(title, *sections)


## TODO: hwo to lexicalise this given that NLG does know about tasks?
#def lexicalise_task(task, document):
#    """ Convert a task to a syntax tree with lexical items in it. """
#    get_log().debug('Lexicalising task %s' % str(task))
#    params = task.input_params[:]
#    key = task.name
#    sent = templates.template(key)
#    if None is sent:
#        sent = templates.template(task.id)
#    if None != sent:
#        _replace_placeholders_with_params(sent, params)
#    else:
#        print('Key "%s" or id "%s" not found' % (task.name, task.id))
#    return sent
#
#
#def _replace_placeholders_with_params(template, params):
#    get_log().debug('Replacing params in template:\n%s' % str(template))
#    get_log().debug('Params: \n\t %s' % str(params))
#    for c in sentence_iterator(template):
#        if (isinstance(c, PlaceHolder)):
#            id = c.id
#            var = params[id]
#            c.object = var
##           print('Replacing parameter %d with %s' % (id, var))

def create_template_from(string):
    return eval(string)





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

RecordData = VP('record', 'data', 'using the kill sheet')
#PP('on', 'success', VP('assert', 'well_shut')))

sat = None#PP('on', 'success', VP('assert', 'kick_killed'))

WaitAndWeight = VP('kill', 'the kick', 'using the Wait and Weight method')
DrillersMethod = VP('kill', 'the kick', 'using the Driller\'s method')
ReverseCirculation = VP('kill', 'the kick', 'using Reverse Circulation')
Bullheading = VP('kill', 'the kick', 'using Bullheading')

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
        self.templates['simple_message'] = Clause(None, PlaceHolder('val'))

        self.templates['string'] = Clause(None, VP(PlaceHolder('val')))
        self.templates['conjunction'] = None
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
        self.templates['long_runway_required'] = 'long runway is required'
        self.templates['high_fuel_consumption'] = 'high fuel consumption'
        self.templates['batB'] = 'it is a better alternative than B'
        self.templates['batA'] = 'it is a better alternative than A'
        self.templates['slsA'] = 'site A is a suitable landing site'
        self.templates['slsB'] = 'site B is a suitable landing site'
        self.templates['CofG'] = 'the centre of gravity shifted'
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
        
        self.templates['drive_to_Edinburgh'] = Clause(you, VP('drive to', 'Edinburgh'))
        self.templates['drive_to_Perth'] = Clause(you, VP('drive to', 'Perth'))
        self.templates['drive_to_Kincardine'] = Clause(you, VP('drive to', 'Kincardine'))
        self.templates['drive_to_Stirling'] = Clause(you, VP('drive to', 'Stirling'))
        self.templates['drive_to_Inverness'] = Clause(you, VP('drive to', 'Inverness'))
        self.templates['drive_to_Aberdeen'] = Clause(you, VP('drive to', 'Aberdeen'))

        self.templates['edinburgh_bridge_closed'] = \
            'Forth Road Bridge outside Edinburgh is closed'
        self.templates['kincardie_bridge_10'] = \
            'the maximum allowed weight on Kincardine Bridge is 10 tons'
        self.templates['vehicle_weight_15'] = \
            'the weight of the vehicle is 15 tons'
        self.templates['traffic_very_slow'] = \
            'the traffic is very slow'
        self.templates['traffic_slow'] = \
            'the traffic is slow'
        self.templates['forecast_old'] = \
            'the forecast is recent'
        self.templates['forecast_high_wind'] = \
            'the weather forecast indicates high winds'
        self.templates['forecast_high_snow'] = \
            'the weather forecast indicates high snow fall'
        self.templates['accident'] = \
            'an accident'
        # TODO: fix the cheet with the preposition: eg. if template is NP, add 'of'
        self.templates['accident_on_bridge'] = \
            'of an accident on the bridge'
        self.templates['stirling_faster'] = \
            'going through Stirling is faster'
        self.templates['kincardine_faster'] = \
            'going through Kincardine is faster'
        self.templates['kincardine_better'] = \
            'going through Kincardine is better'
        self.templates['stirling_shorter'] = \
            'going through Stirling is faster'
        self.templates['kincardine_shorter'] = \
            'going through Kincardine is faster'

        self.templates['can_Edinburgh_to_Stirling'] = \
            'you can go from Edinburgh to Stirling'
        self.templates['can_Edinburgh_to_Kincardine'] = \
            'you can go from Edinburgh to Kincardine'
        self.templates['can_Edinburgh_to_Perth'] = \
            'you can go from Edinburgh to Perth'
        self.templates['can_Stirling_to_Perth'] = \
            'you can go from Stirling to Perth'
        self.templates['can_Perth_to_Aberdeen'] = \
            'you can go from Perth to Aberdeen'
        self.templates['can_Perth_to_Inverness'] = \
            'you can go from Perth to Inverness'
        self.templates['can_Aberdeen_to_Inverness'] = \
            'you can go from Aberdeen to Inverness'
        self.templates['can_Aberdeen_to_Perth'] = \
            'you can go from Aberdeen to Perth'
        self.templates['can_Inverness_to_Aberdeen'] = \
            'you can go from Inverness to Aberdeen'
        self.templates['can_Inverness_to_Perth'] = \
            'you can go from Inverness to Perth'
        self.templates['can_Perth_to_Stirling'] = \
            'you can go from Perth to Stirling'
        self.templates['can_Perth_to_Kincardine'] = \
            'you can go from Perth to Kincardine'
        self.templates['can_Perth_to_Edinburgh'] = \
            'you can go from Perth to Edinburgh'
        self.templates['can_Kincardine_to_Edinburgh'] = \
            'you can go from Kincardine to Edinburgh'
        self.templates['can_Stirling_to_Edinburgh'] = \
            'you can go from Stirling to Edinburgh'

        self.templates['edinburgh_stirling_not_possible'] = \
            'you cannot go from Edinburgh to Stirling'
        self.templates['edinburgh_kincardine_not_possible'] = \
            'you cannot go from Edinburgh to Kincardine'
        self.templates['edinburgh_perth_not_possible'] = \
            'you cannot go from Edinburgh to Perth'
        self.templates['stirling_perth_not_possible'] = \
            'you cannot go from Stirling to Perth'
        self.templates['perth_aberdeen_not_possible'] = \
            'you cannot go from Perth to Aberdeen'
        self.templates['perth_inverness_not_possible'] = \
            'you cannot go from Inverness to Inverness'
        self.templates['aberdeen_inverness_not_possible'] = \
            'you cannot go from Aberdeen to Inverness'
        self.templates['aberdeen_perth_not_possible'] = \
            'you cannot go from Aberdeen to Perth'
        self.templates['inverness_aberdeen_not_possible'] = \
            'you cannot go from Inverness to Aberdeen'
        self.templates['inverness_perth_not_possible'] = \
            'you cannot go from Inverness to Perth'
        self.templates['perth_stirling_not_possible'] = \
            'you cannot go from Perth to Stirling'
        self.templates['perth_kincardine_not_possible'] = \
            'you cannot go from Perth to Kincardine'
        self.templates['perth_edinburgh_not_possible'] = \
            'you cannot go from Perth to Edinburgh'
        self.templates['kincardine_edinburgh_not_possible'] = \
            'you cannot go from Kincardine to Edinburgh'
        self.templates['stirling_edinburgh_not_possible'] = \
            'you cannot go from Stirling to Edinburgh'

        self.templates['Stirling1'] = 'go to Stirling'
        self.templates['Stirling2'] = 'go to Stirling'
        self.templates['Edinburgh1'] = 'go to Edinburgh'
        self.templates['Edinburgh2'] = 'go to Edinburgh'
        self.templates['Aberdeen1'] = 'go to Aberdeen'
        self.templates['Aberdeen2'] = 'go to Aberdeen'
        self.templates['Inverness1'] = 'go to Inverness'
        self.templates['Inverness2'] = 'go to Inverness'
        self.templates['Perth1'] = 'go to Perth'
        self.templates['Perth2'] = 'go to Perth'
        self.templates['Kincardine1'] = 'go to Kincardine'
        self.templates['Kincardine2'] = 'go to Kincardine'

        self.templates['system_malfunction'] = 'system malfunction'
        self.templates['require_immediate_landing'] = \
            'UAV requires immediate landing'
        self.templates['-ilsA'] = \
            'no Instrumental Landing System detected at airfield A'
        self.templates['-ilsB'] = \
            'no Instrumental Landing System detected at airfield B'
        self.templates['-vlpA'] = \
            'no visual landing at airfield A possible'
        self.templates['lvA'] = \
            'low visibility at airfield A'
        self.templates['-alpA'] = \
            'no automated landing possible at airfield A'

        self.templates['ilsA'] = \
            'Instrumental Landing System detected at airfield A'
        self.templates['ilsB'] = \
            'Instrumental Landing System detected at airfield B'
        self.templates['vlpA'] = \
            'visual landing at airfield A possible'
        self.templates['alpA'] = \
            'automated landing possible at airfield A'
        self.templates['vlpB'] = \
            'visual landing at airfield B possible'
        self.templates['alpB'] = \
            'automated landing possible at airfield B'

        self.templates['kick'] = 'a kick was detected'
        self.templates['need_speed'] = 'the well has to be shut quickly'
        self.templates['shallow_depth'] = 'the well is in a shallow depth'
        self.templates['do_kill'] = 'kill the kick'
        self.templates['HSP_very_low'] = 'HSP is very low'

        self.templates['OpenChokeLine'] =\
            Clause(NP('you'), VP('open choke line'))
        self.templates['CollarsInBOP'] =\
            Clause(NP('you'), VP('collars in bop'))
        self.templates['InstallKillAssemblyAndTest'] =\
            Clause(NP('you'), VP('install kill assembly and test'))
        self.templates['CheckSpaceOut'] =\
            Clause(NP('you'), VP('check space out'))
        self.templates['ClosePipeRams'] =\
            Clause(NP('you'), VP('close pipe rams'))
        self.templates['LandStringAndClosePosilocks'] =\
            Clause(NP('you'), VP('land string and close posilocks'))
        self.templates['OpenKellyCock'] =\
            Clause(NP('you'), VP('open kelly cock'))
        self.templates['CheckSurfacePressures'] =\
            Clause(NP('you'), VP('check surface pressures'))
        self.templates['CheckUpwardForce'] =\
            Clause(NP('you'), VP('check upward force'))
        self.templates['DropStringThenCloseShearRams'] =\
            Clause(NP('you'), VP('drop string then close shear rams'))
        self.templates['ObserveWell'] =\
            Clause(NP('you'), VP('observe well'))
        self.templates['MusterAllCrewsForInformation'] =\
            Clause(NP('you'), VP('muster all crews for information'))
        self.templates['PrepareToKillWell'] =\
            Clause(NP('you'), VP('prepare to kill well'))

    def template(self, action):
        if action in self.templates:
            return deepcopy(self.templates[action])
        else:
            return None


templates = SentenceTemplates()

def add_templates(newtemplates):
    """ Add the given templates to the default SentenceTemplate instance. """
    for k, v in newtemplates:
        templates.templates[k] = v

def add_template(k, v, replace=True):
    if replace or (not k in templates.templates):
        templates.templates[k] = v
        return True
    else:
        return False

def del_template(k, silent=True):
    if silent and k not in templates.templates: return False
    del templates.templates[k]





