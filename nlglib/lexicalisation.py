import numbers

from nlglib import realisation
from nlglib.aggregation import *
from nlglib.lexicon import *
from nlglib.microplanning import *


def get_log():
    return logging.getLogger(__name__)


get_log().addHandler(logging.NullHandler())


def lexicalise(msg, **kwargs):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, numbers.Number):
        return Numeral(msg)
    elif isinstance(msg, str):
        return String(msg)
    elif isinstance(msg, (list, tuple)):
        return [lexicalise(x, **kwargs) for x in msg]
    elif isinstance(msg, Element):
        return lexicalise_element(msg, **kwargs)
    elif isinstance(msg, MsgSpec):
        return lexicalise_message_spec(msg, **kwargs)
    elif isinstance(msg, Message):
        return lexicalise_message(msg, **kwargs)
    elif isinstance(msg, Paragraph):
        return lexicalise_paragraph(msg, **kwargs)
    elif isinstance(msg, Section):
        return lexicalise_section(msg, **kwargs)
    elif isinstance(msg, Document):
        return lexicalise_document(msg, **kwargs)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)


def lexicalise_element(elt, **kwargs):
    """ See if element contains placeholders and if so, replace them
    by templates.

    """
    get_log().debug('Lexicalising Element: {0}'.format(repr(elt)))
    available_templates = kwargs.get('templates', templates)
    # find arguments
    args = elt.arguments()
    # if there are any arguments, replace them by values
    for arg in args:
        result = available_templates.template(arg.id)
        if result is None: continue
        get_log().debug('Replacing\n{0} in \n{1} by \n{2}.'
                        .format(repr(arg), repr(elt), repr(result)))
        if isinstance(result, str):
            result = String(result)
        result.add_features(elt._features)
        if elt == arg:
            return result
        else:
            elt.replace(arg, lexicalise(result, **kwargs))
    return elt


# each message should correspond to a clause
def lexicalise_message_spec(msg, **kwargs):
    """ Return Element corresponding to given message specification.
    If the lexicaliser can not find correct lexicalisation, it returns None
    and logs the error.

    """
    get_log().debug('Lexicalising message specs: {0}'.format(repr(msg)))
    available_templates = kwargs.get('templates', templates)
    template = None
    try:
        template = available_templates.template(msg.name)
        # TODO: should MessageSpec correspond to a clause?
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
            # check if value is a template
            if isinstance(val, Word) or isinstance(val, String):
                t = templates.template(val.string)
                if t:
                    val = t
            get_log().debug(' val = {0}'.format(repr(val)))
            template.replace(arg, lexicalise(val, **kwargs))
        return template
    except Exception as e:
        get_log().exception(str(e))
        get_log().info('\tmessage: ' + repr(msg))
        get_log().info('\ttemplate: ' + repr(template))


# TODO: lexicalisation should replace Messages by {NLG Elements} and use
# RST relations to connect the clauses when applicable.
def lexicalise_message(msg, parenthesis=False, **kwargs):
    """ Return a copy of Message with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising message {0}'.format(msg))
    if msg is None: return None
    if isinstance(msg.nucleus, list):
        nucleus = [lexicalise(x, **kwargs) for x in msg.nucleus if x is not None]
    else:
        nucleus = lexicalise(msg.nucleus, **kwargs)
    satellites = [lexicalise(x, **kwargs) for x in msg.satellites if x is not None]

    features = msg._features if hasattr(msg, '_features') else {}
    # stick each message into a clause
    result = None
    if msg.rst == 'Conjunction' or msg.rst == 'Disjunction':
        result = Coordination(*satellites, conj=msg.marker, features=features)
    elif msg.rst == 'Imply':
        get_log().debug('RST Implication: ' + repr(msg))
        subj = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satellites[0])
        compl.set_feature('COMPLEMENTISER', 'then')
        result = subj
        result.add_complement(compl)
        result.add_front_modifier('if')
    elif msg.rst == 'Equivalent':
        result = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satellites[0])
        compl.set_feature('COMPLEMENTISER', 'if and only if')
        result.add_complement(compl)
    elif msg.rst == 'ImpliedBy':
        result = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satellites[0])
        compl.set_feature('COMPLEMENTISER', 'if')
        result.add_complement(compl)
    elif msg.rst == 'Unless':
        result = promote_to_phrase(nucleus)
        compl = promote_to_phrase(satellites[0])
        compl.set_feature('COMPLEMENTISER', 'unless')
        result.add_complement(compl)
    elif msg.rst == 'Equality':
        result = Clause()
        result.set_subj(nucleus)
        object = satellites[0]
        tmp_vp = VP('is', object, features=features)
        get_log().debug('Setting VP:\n' + repr(tmp_vp))
        result.set_vp(tmp_vp)
    elif msg.rst == 'Inequality':
        result = Clause()
        result.set_subj(nucleus)
        object = satellites[0]
        features['NEGATED'] = 'true'
        result.set_vp(VP('is', object, features=features))
    elif msg.rst == 'Quantifier':
        # quantifiers have multiple nuclei (variables)
        quant = msg.marker
        cc = Coordination(*nucleus, conj='and')
        np = NounPhrase(cc, String(quant))

        if quant.startswith('there exist'):
            np.add_post_modifier(String('such that'))
        else:
            np.add_post_modifier(String(','))

        result = promote_to_phrase(satellites[0])

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
        get_log().debug('RST satellite: ' + repr(satellites))
        result = Message(msg.rst, nucleus, *satellites)
        result.marker = msg.marker
        # TODO: decide how to handle features. Add to all? Drop?
        # return ([nucleus] if nucleus else []) + [x for x in satellites]
    result.add_features(features)
    return result


def lexicalise_paragraph(msg, **kwargs):
    """ Return a copy of Paragraph with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising paragraph.')
    if msg is None: return None
    messages = [lexicalise(x, **kwargs) for x in msg.messages if x is not None]
    return Paragraph(*messages)


def lexicalise_section(msg, **kwargs):
    """ Return a copy of a Section with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising section.')
    if msg is None: return None
    title = lexicalise(msg.title, **kwargs)
    paragraphs = [lexicalise(x, **kwargs) for x in msg.content if x is not None]
    return Section(title, *paragraphs)


def lexicalise_document(doc, **kwargs):
    """ Return a copy of a Document with MsgSpecs replaced by NLG Elements. """
    get_log().debug('Lexicalising document.')
    if doc is None: return None
    title = lexicalise(doc.title, **kwargs)
    sections = [lexicalise(x, **kwargs) for x in doc.sections if x is not None]
    return Document(title, *sections)


def create_template_from(string):
    return eval(string)


class SentenceTemplates:
    """SentenceTemplates provides mapping from STRIPS operators to sentences.
        The keys are actionN where N is the number of parameters. These
        are mapped to string compatible with string.format().
    """

    def __init__(self):
        self.templates = dict()
        self.templates['simple_message'] = Clause(None, PlaceHolder('val'))
        self.templates['string'] = Clause(None, VerbPhrase(PlaceHolder('val')))

    def template(self, action):
        if action in self.templates:
            return deepcopy(self.templates[action])
        else:
            return None


templates = SentenceTemplates()


def add_templates(newtemplates):
    """ Add the given templates to the default SentenceTemplate instance. """
    for k, v in newtemplates.items():
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


def string_to_template(s):
    return eval(s)
