from copy import deepcopy
import logging
import numbers

from nlg.structures import *
from nlg.aggregation import *
from nlg.microplanning import *
import nlg.realisation as realisation

def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())


def lexicalise(msg):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, numbers.Number):
        return numeral(msg)
    elif isinstance(msg, str):
        return String(msg)
    elif isinstance(msg, Element):
        return lexicalise_element(msg)
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


def lexicalise_element(elt):
    """ See if element contains placeholders and if so, replace them
    by templates.

    """
    get_log().debug('Lexicalising Element: {0}'.format(repr(elt)))
    # find arguments
    args = elt.arguments()
    # if there are any arguments, replace them by values
    for arg in args:
        result = templates.template(arg.id)
        if result is None: continue
        get_log().debug('Replacing\n{0} in \n{1} by \n{2}.'
                        .format(repr(arg), repr(elt), repr(result)))
        if isinstance(template, str):
            result = String(result)
        result.add_features(elt._features)
        if elt == arg:
            return result
        else:
            elt.replace(arg, lexicalise(result))
    return elt

# each message should correspond to a clause
def lexicalise_message_spec(msg):
    """ Return Element corresponding to given message specification.
    If the lexicaliser can not find correct lexicalisation, it returns None
    and logs the error.

    """
    get_log().debug('Lexicalising message specs: {0}'.format(repr(msg)))
    try:
        template = templates.template(msg.name)
        if template is None:
            get_log().warning('No sentence template for "%s"' % msg.name)
            result = String(str(msg))
            result.add_features(msg._features)
            return result
        if isinstance(template, str):
            result = String(template)
            result.add_features(msg._features)
            return result
        template.add_features(msg._features)
        # find arguments
        args = template.arguments()
        # if there are any arguments, replace them by values
        # TODO: check that features are propagated
        for arg in args:
            get_log().debug('Replacing\n{0} in \n{1}.'
                            .format(str(arg), repr(template)))
            val = msg.value_for(arg.id)
            get_log().debug(' val = {0}'.format(repr(val)))
            template.replace(arg, lexicalise(val))
        return template
    except Exception as e:
        get_log().exception(str(e))
        get_log().info('\tmessage: ' + repr(msg))
        get_log().info('\ttemplate: ' + repr(template))


# TODO: lexicalisation should replace Messages by {NLG Elements} and use
# RST relations to connect the clauses when applicable.
def lexicalise_message(msg, parenthesis=False):
    """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising message.')
    if msg is None: return None
    if isinstance(msg.nucleus, list):
        nucleus = [lexicalise(x) for x in msg.nucleus if x is not None]
    else:
        nucleus = lexicalise(msg.nucleus)
    satelites = [lexicalise(x) for x in msg.satelites if x is not None]

    features = msg._features if hasattr(msg, '_features') else {}
    # stick each message into a clause
    result = None
    if msg.rst == 'Conjunction' or msg.rst == 'Disjunction':
        result = Coordination(*satelites, conj=msg.marker, features=features)
    elif msg.rst == 'Imply':
        subj = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satelites[0])
        compl.set_feature('COMPLEMENTISER', 'then')
        result = subj
        result.add_complement(compl)
        result.add_front_modifier('if')
    elif msg.rst == 'Equivalent':
        result = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satelites[0])
        compl.set_feature('COMPLEMENTISER', 'if and only if')
        result.add_complement(compl)
    elif msg.rst == 'ImpliedBy':
        result = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satelites[0])
        compl.set_feature('COMPLEMENTISER', 'if')
        result.add_complement(compl)
    elif msg.rst == 'Equality':
        result = Clause()
        result.set_subj(nucleus)
        object = satelites[0]
        tmp_vp = VP('equal', object, features=features)
        get_log().debug('Setting VP:\n' + repr(tmp_vp))
        result.set_vp(tmp_vp)
    elif msg.rst == 'Inequality':
        result = Clause()
        result.set_subj(nucleus)
        object = satelites[0]
        features['NEGATED'] = 'true'
        result.set_vp(VP('equal', object, features=features))
    elif msg.rst == 'Quantifier':
        # quantifiers have multiple nuclei (variables)
        quant = msg.marker
        cc = Coordination(*nucleus, conj='and')
        np = NounPhrase(cc, String(quant))

        if (quant.startswith('there exist')):
            np.add_post_modifier(String('such that'))
        else:
            np.add_post_modifier(String(','))

        result = promote_to_phrase(satelites[0])

        front_mod = realisation.simple_realisation(np)
        # remove period
        if front_mod.endswith('.'): front_mod = front_mod[:-1]
        # lower case the first letter
        front_mod = front_mod[0].lower() + front_mod[1:]
        # front_mod should go in front of existing front_mods
        # In case of CC, modify the first coordinate
        if result._type == COORDINATION:
            result.coords[0].add_front_modifier(String(front_mod), pos=0)
        else:
            result.add_front_modifier(String(front_mod), pos=0)
        get_log().debug('Result:\n' + repr(result))
    elif msg.rst == 'Negation':
        result = Clause(Pronoun('it'), VP('is', NP('the', 'case'),
                                          features={'NEGATED': 'true'}))
        cl = promote_to_phrase(nucleus)
        cl.set_feature('COMPLEMENTISER', 'that')
        if parenthesis:
            cl.add_front_modifier('(')
            cl.add_post_modifier(')')
        result.vp.add_complement(cl)
    else:
        get_log().debug('RST relation: ' + repr(msg))
        get_log().debug('RST nucleus:  ' + repr(nucleus))
        get_log().debug('RST satelite: ' + repr(satelites))
        result = Message(msg.rst, nucleus, *satelites)
        result.marker = msg.marker
        # TODO: decide how to handle features. Add to all? Drop?
        #return ([nucleus] if nucleus else []) + [x for x in satelites]
    result.add_features(features)
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

you = Element() # Word('you', 'PRONOUN')

load_truck = Clause(you, VerbPhrase(put, PlaceHolder(0), PrepositionalPhrase(into, PlaceHolder(1))))
drive_truck = Clause(you, VerbPhrase(drive, PlaceHolder(0),
                                     PrepositionalPhrase(from_, PlaceHolder(1)),
                                     PrepositionalPhrase(to, PlaceHolder(2))))
unload_truck = Clause(you, VerbPhrase(unload, PlaceHolder(0),
                                       PrepositionalPhrase(from_, PlaceHolder(1))))
load_airplane = Clause(you, VerbPhrase(put, PlaceHolder(0),
                                      PrepositionalPhrase(into, PlaceHolder(1))))

fly_airplane = deepcopy(drive_truck)
fly_airplane.vp.head = fly
unload_airplane = unload_truck

move = Clause(you, VerbPhrase(move, [PlaceHolder(0),
                             PrepositionalPhrase(from_, PlaceHolder(1)),
                             PrepositionalPhrase(to, PlaceHolder(2)),
                             VerbPhrase(using, PlaceHolder(3))]))

start = Clause(you, VerbPhrase(Word('start', 'VERB')))
finish = Clause(you, VerbPhrase(Word('finish', 'VERB')))


# UAV domain

uav = Word('UAV', 'NOUN')
takeOff = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('taking off', 'VERB')))
flyToTargetArea = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('flying to the target area', 'VERB')))
takePhotos = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('taking photos', 'VERB')))
selectLandingSite = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('selecting landing site', 'VERB')))
flyToAirfieldA = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('flying to airfield A', 'VERB')))
flyToAirfieldB = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('flying to airfield B', 'VERB')))
flyToBase = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('flying to the base', 'VERB')))
Land = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('landing', 'VERB')))
SelectRunway = Clause(uav, VerbPhrase(Word('is', 'VERB'), 'selecting a runway'))
LandOnLongRunway = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('landing', 'VERB'), PrepositionalPhrase('on', 'a long runway')))
LandOnShortRunway = Clause(uav, VerbPhrase(Word('is', 'VERB'), Word('landing', 'VERB'), PrepositionalPhrase('on', 'a short runway')))

# Workflow summary phrase specifications
the_workflow = NounPhrase(spec='the', head='workflow')
SummariseNumTasks = Clause(the_workflow,
                        VerbPhrase('has', PlaceHolder('arg_num_steps'), 'tasks'))
SummariseNumChoices = Clause(the_workflow,
                        VerbPhrase('has', PlaceHolder('arg_num_choices'), 'choices'))


# KickDetection
Drill = VerbPhrase('drill')
Trip = VerbPhrase('perform', 'tripping')
AdjustHSP = VerbPhrase('adjust', 'HSP')
Monitor = VerbPhrase('check', 'sensors')
SoftShutIn = VerbPhrase('perform', 'soft', 'shut-in')
HardShutIn = VerbPhrase('perform', 'hard', 'shut-in')

RecordData = Message('Elaboration',
                     VerbPhrase('record', 'data', 'using the kill sheet'),
                     None)#PrepositionalPhrase('on', 'success', VerbPhrase('assert', 'well_shut')))

sat = None#PrepositionalPhrase('on', 'success', VerbPhrase('assert', 'kick_killed'))

WaitAndWeight = Message('Ellaboration',
    VerbPhrase('kill', 'the kick', 'using the Wait and Weight method'), sat)
DrillersMethod = Message('Ellaboration',
    VerbPhrase('kill', 'the kick', 'using the Driller\'s method'), sat)
ReverseCirculation = Message('Ellaboration',
    VerbPhrase('kill', 'the kick', 'using Reverse Circulation'), sat)
Bullheading = Message('Ellaboration',
    VerbPhrase('kill', 'the kick', 'using Bullheading'), sat)

RecordData = VerbPhrase('record', 'data', 'using the kill sheet')
#PrepositionalPhrase('on', 'success', VerbPhrase('assert', 'well_shut')))

sat = None#PrepositionalPhrase('on', 'success', VerbPhrase('assert', 'kick_killed'))

WaitAndWeight = VerbPhrase('kill', 'the kick', 'using the Wait and Weight method')
DrillersMethod = VerbPhrase('kill', 'the kick', 'using the Driller\'s method')
ReverseCirculation = VerbPhrase('kill', 'the kick', 'using Reverse Circulation')
Bullheading = VerbPhrase('kill', 'the kick', 'using Bullheading')

ReopenWell = VerbPhrase('reopen', 'the well')

SealWell = VerbPhrase('seal', 'the well')
PlugWell = VerbPhrase('plug', 'the well')

EmergencyTask = NounPhrase('emergency taks')
NormalTask = NounPhrase('task')

Need_speed = Clause(NounPhrase('the well'), VerbPhrase('has to be shut quickly'))

kick = Clause(NounPhrase('a kick'), VerbPhrase('was detected'))

shallow_depth = Clause(NounPhrase('the well'), VerbPhrase('is in shallow depth'))


class SentenceTemplates:
    """SentenceTemplates provides mapping from STRIPS operators to sentences.
        The keys are actionN where N is the number of parameters. These
        are mapped to string compatible with string.format().
    """

    def __init__(self):
        self.templates = dict()
        self.templates['simple_message'] = Clause(None, PlaceHolder('val'))

        self.templates['string'] = Clause(None, VerbPhrase(PlaceHolder('val')))
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
        self.templates['Edinburgh'] = Clause(you, VerbPhrase('drive to', 'Edinburgh'))
        self.templates['Perth'] = Clause(you, VerbPhrase('drive to', 'Perth'))
        self.templates['Kincardine'] = Clause(you, VerbPhrase('drive to', 'Kincardine'))
        self.templates['Stirling'] = Clause(you, VerbPhrase('drive to', 'Stirling'))
        self.templates['Inverness'] = Clause(you, VP('drive', PP('to', NNP('Inverness'))))
        self.templates['Aberdeen'] = Clause(you, VerbPhrase('drive to', 'Aberdeen'))

        self.templates['drive_to_Edinburgh'] = Clause(you, VerbPhrase('drive to', 'Edinburgh'))
        self.templates['drive_to_Perth'] = Clause(you, VerbPhrase('drive to', 'Perth'))
        self.templates['drive_to_Kincardine'] = Clause(you, VerbPhrase('drive to', 'Kincardine'))
        self.templates['drive_to_Stirling'] = Clause(you, VerbPhrase('drive to', 'Stirling'))
        self.templates['drive_to_Inverness'] = Clause(you, VerbPhrase('drive to', 'Inverness'))
        self.templates['drive_to_Aberdeen'] = Clause(you, VerbPhrase('drive to', 'Aberdeen'))

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
        # TODO: fix the cheet with the preposition: eg. if template is NounPhrase, add 'of'
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
            Clause(NounPhrase('you'), VerbPhrase('open choke line'))
        self.templates['CollarsInBOP'] =\
            Clause(NounPhrase('you'), VerbPhrase('collars in bop'))
        self.templates['InstallKillAssemblyAndTest'] =\
            Clause(NounPhrase('you'), VerbPhrase('install kill assembly and test'))
        self.templates['CheckSpaceOut'] =\
            Clause(NounPhrase('you'), VerbPhrase('check space out'))
        self.templates['ClosePipeRams'] =\
            Clause(NounPhrase('you'), VerbPhrase('close pipe rams'))
        self.templates['LandStringAndClosePosilocks'] =\
            Clause(NounPhrase('you'), VerbPhrase('land string and close posilocks'))
        self.templates['OpenKellyCock'] =\
            Clause(NounPhrase('you'), VerbPhrase('open kelly cock'))
        self.templates['CheckSurfacePressures'] =\
            Clause(NounPhrase('you'), VerbPhrase('check surface pressures'))
        self.templates['CheckUpwardForce'] =\
            Clause(NounPhrase('you'), VerbPhrase('check upward force'))
        self.templates['DropStringThenCloseShearRams'] =\
            Clause(NounPhrase('you'), VerbPhrase('drop string then close shear rams'))
        self.templates['ObserveWell'] =\
            Clause(NounPhrase('you'), VerbPhrase('observe well'))
        self.templates['MusterAllCrewsForInformation'] =\
            Clause(NounPhrase('you'), VerbPhrase('muster all crews for information'))
        self.templates['PrepareToKillWell'] =\
            Clause(NounPhrase('you'), VerbPhrase('prepare to kill well'))

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
