import re
from copy import deepcopy

from nlg.structures import *

class Context:
    def __init__(self, ontology=None):
        self.ontology = ontology
        self.referents = dict()
        self.last_referent = None


def generate_re(msg, context):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, str):
        print('_attempted to gre for a string. ')
        return msg
    elif isinstance(msg, MsgSpec):
        print('_attempted to gre for a MsgSpec. ')
        return msg
    elif isinstance(msg, Element):
        return generate_re_element(msg, context)
    elif isinstance(msg, Message):
        return generate_re_message(msg, context)
    elif isinstance(msg, Paragraph):
        return generate_re_paragraph(msg, context)
    elif isinstance(msg, Section):
        return generate_re_section(msg, context)
    elif isinstance(msg, Document):
        return generate_re_document(msg, context)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance')


def generate_re_element(element, context):
    print('^^^ called generate_re_element')
    element = deepcopy(element)
    _replace_placeholders_with_nps(element, context)
    return element


def generate_re_message(msg, context):
    print('^^^ called generate_re_message')
    if msg is None: return None
    nucleus = generate_re(msg.nucleus, context)
    satelites = [generate_re(x, context) \
                    for x in msg.satelites if x is not None]
    return Message(msg.rst, nucleus, *satelites)


def generate_re_paragraph(para, context):
    print('^^^ called generate_re_paragraph')
    if para is None: return None
    messages = [generate_re(x, context) \
                   for x in para.messages if x is not None]
    return Paragraph(*messages)


def generate_re_section(sec, context):
    print('^^^ called generate_re_section')
    if sec is None: return None
    title = generate_re(sec.title, context)
    paragraphs = [generate_re(x, context) \
                    for x in sec.paragraphs if x is not None]
    return Section(title, *paragraphs)


def generate_re_document(doc, context):
    """ Iterate through a Document and replace all PlaceHolders by
    referring expressions. 
    
    """
    print('^^^ called generate_re_document')
    if doc is None: return None
    title = generate_re(doc.title, context)
    sections = [generate_re(x, context) \
                   for x in doc.sections if x is not None]
    return Document(title, *sections)


#def gre(msgs, context):
#    """ Replace placeholders with NPs
#    The placeholders should already have names in them, so just replace
#    each of them by an NP.
#    
#    """
#    if context is None: context = Context(document.ontology)
#
#    messages = deepcopy(msgs)
#    for m in messages:
#        _replace_placeholders_with_nps(m, context)
#    return messages

def _replace_placeholders_with_nps(message, context):
    for arg in message.arguments():
        refexp = generate_ref_exp(str(arg.value), context)
        replace_element(message, arg, refexp)


# copied from REG class in NLG - perhaps deprecated?

def generate_ref_exp(referent, context):
    # can we use a pronoun?
    # actually, using a pronoun for the last ref can still be ambiguous :-)
#        if referent == context.last_referent:
#            return NP(Word('it', 'PRONOUN'))

    result = None

    if referent in context.referents:
        result = _do_repeated_reference(referent, context)
    else:
        result = _do_initial_reference(referent, context)
    return result

def _do_initial_reference(referent, context):
    result = None

    # do we have information about the referent?
    try:
        onto = context.ontology
        if onto is None: print('GRE does not have ontology!')

        entity_type = onto.best_entity_type(':' + referent)
        result = NP(Word(entity_type, 'NOUN'))
        print('\t%s: type "%s"' % (referent, entity_type))
        # if the object is the only one in the domain, add 'the'
        distractors = onto.entities_of_type(':' + entity_type)
        print('\tdistractors: %s' % str(distractors))
        count = len(distractors)

        if count == 1:
            # save the RE without the determiner
            context.referents[referent] = (True, deepcopy(result))
            # this should really be done by simpleNLG...
            if entity_type[0] in "aeiouy":
                result.spec = Word('an', 'DETERMINER')
            else:
                result.spec = Word('a', 'DETERMINER')
        else:
            context.referents[referent] = (False, result)
            # else add the number to distinguish from others
            number = None
            tmp = re.search(r"([^0-9]+)([0-9]+)$", referent)
            if (tmp is not None):
                number = tmp.group(2)

            if (number is not None):
                result.add_complement(Word(number))
    except Exception as msg:
        # if we have no info, assume referent is not unique
        result = NP(Word(referent, 'NOUN'))
        context.referents[referent] = (False, result)
        print('GRE for "%s" failed : "%s"' % (referent, str(msg)))

    context.last_referent = referent
    return result

def _do_repeated_reference(referent, context):
    result = None

    is_unique, re = context.referents[referent]
    if is_unique:
        result = deepcopy(re)
        result.spec = Word('the', 'DETERMINER')
    else:
        result = re
    return result

def _count_type_instances(entity_type, object_map):
    count = 0
    for k, v in object_map.items():
        if v == entity_type: count += 1
    return count
