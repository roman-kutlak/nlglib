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


import re
from copy import deepcopy
import logging

from nlg.structures import *


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


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
        get_log().warning('_attempted to gre for a string. ')
        return msg
    elif isinstance(msg, MsgSpec):
        get_log().warning('_attempted to gre for a MsgSpec. ')
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
        raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)


def generate_re_element(element, context):
    get_log().debug('Generating RE for element.')
    element = deepcopy(element)
    _replace_placeholders_with_nps(element, context)
    return element


def generate_re_message(msg, context):
    get_log().debug('Generating RE for message.')
    if msg is None: return None
    nucleus = generate_re(msg.nucleus, context)
    satelites = [generate_re(x, context) \
                    for x in msg.satelites if x is not None]
    return Message(msg.rst, nucleus, *satelites)


def generate_re_paragraph(para, context):
    get_log().debug('Generating RE for paragraph.')
    if para is None: return None
    messages = [generate_re(x, context) \
                   for x in para.messages if x is not None]
    return Paragraph(*messages)


def generate_re_section(sec, context):
    get_log().debug('Generating RE for section.')
    if sec is None: return None
    title = generate_re(sec.title, context)
    paragraphs = [generate_re(x, context) \
                    for x in sec.paragraphs if x is not None]
    return Section(title, *paragraphs)


def generate_re_document(doc, context):
    """ Iterate through a Document and replace all PlaceHolders by
    referring expressions. 
    
    """
    get_log().debug('Generating RE for document.')
    if doc is None: return None
    title = generate_re(doc.title, context)
    sections = [generate_re(x, context) \
                   for x in doc.sections if x is not None]
    return Document(title, *sections)


def _replace_placeholders_with_nps(message, context):
    get_log().debug('Replacing placeholders.')
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

    get_log().debug('GRE for %s:' % str(referent))
    get_log().debug('\treferents: %s' % str(context.referents))
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
        if onto is None:
            get_log().warning('GRE does not have ontology!')

        entity_type = onto.best_entity_type(':' + referent)
        entity_type = entity_type[1:] # strip the ':' at the beginning
        result = NP(Word(entity_type, 'NOUN'))
        get_log().debug('\t%s: type "%s"' % (referent, entity_type))
        # if the object is the only one in the domain, add 'the'
        distractors = onto.entities_of_type(':' + entity_type)
        get_log().debug('\tdistractors: %s' % str(distractors))
        count = len(distractors)

        if count == 1:
            # save the RE without the determiner
            context.referents[referent] = (True, deepcopy(result))
            # this should really be done by simpleNLG...
#            if entity_type[0] in "aeiouy":
#                result.spec = Word('an', 'DETERMINER')
#            else:
#                result.spec = Word('a', 'DETERMINER')
            # use definite reference even when the object appears 1st time
            result.spec = Word('the', 'DETERMINER')
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
        get_log().debug('GRE for "%s" failed : "%s"' % (referent, str(msg)))

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
