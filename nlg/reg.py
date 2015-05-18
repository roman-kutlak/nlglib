
import re
from copy import deepcopy, copy
import logging

from nlg.structures import *
from nlg.microplanning import replace_element, replace_element_with_id
import nlg.lexicon as lexicon
from nlg.lexicon import Case, NP, Pronoun, Gender, Features, PronounUse, Number


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


class Context:
    def __init__(self, ontology=None):
        self.ontology = ontology
        self.referents = dict()
        self.referent_stack = []
        self.history = []
        self.rfexps = []

    def add_sentence(self, sent):
        """Add a sentence to the context. """
        self.history.append(sent)
        # add potential referents/distractors
        self._update_referents(sent)

    def _update_referents(self, sent):
        """Extract NPs and add them on the referent stack. Add subject last. """
        self.referent_stack.extend(
            reversed([x for x in sent.constituents()
                if isinstance(x, NounPhrase) or isinstance(x, Coordination)]))


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
        raise TypeError('"%s" has a wrong type (%s).' %
                        (msg, str(type(msg))))


def generate_re_element(element, context):
    get_log().debug('Generating RE for element.')
    with_refexp = deepcopy(element)
    _replace_placeholders_with_nps(with_refexp, context)
    result = optimise_ref_exp(with_refexp, context)
    return result


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
        ref = arg.value or arg.id
        refexp = generate_ref_exp(ref, context)
        replace_element(message, arg, refexp)
#        arg.set_value(refexp)

def generate_ref_exp(referent, context):
    result = None

    get_log().debug('GRE for "{0}"'.format(referent))
    if not (isinstance(referent, String) or isinstance(referent, Word)):
        return referent
    if referent in context.referents:
        result = _do_repeated_reference(referent, context)
    else:
        result = _do_initial_reference(referent, context)
    return result

def _do_initial_reference(target, context):
    result = None

    # do we have information about the referent?
    try:
        onto = context.ontology
        if onto is None:
            get_log().error('GRE does not have ontology!')
    
        referent = target.string
        # if referent starts with a capital, assume that it is a proper name
        if referent[0].isupper():
            result = NounPhrase(target, features=target._features)
            result.set_feature('PROPER', 'true')
            return result
        
        entity_type = onto.best_entity_type(':' + referent)
        entity_type = entity_type.rpartition(':')[2] # strip the ':' at the beginning
        result = NounPhrase(Word(entity_type, 'NOUN'))
        get_log().debug('\t%s: type "%s"' % (referent, entity_type))
        # if the object is the only one in the domain, add 'the'
        same_type = set([x.rpartition(':')[2] for x in
                         onto.entities_of_type(':' + entity_type)])
        entities = set(context.referents.keys())
        distractors = list(same_type)
#        distractors = list(entities & same_type)
        get_log().debug('\tsame type: %s' % str(same_type))
        get_log().debug('\tentities: %s' % str(entities))
        get_log().debug('\tdistractors: %s' % str(distractors))
        count = len(distractors)
        if count == 0 or (count == 1 and distractors[0] == referent):
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
                result.set_feature('PROPER', 'true')
    except AttributeError:
        result = NounPhrase(target, features=target._features)
        context.referents[target] = (False, result)
    except Exception as msg:
        get_log().exception(msg)
        # if we have no info, assume referent is not unique
        result = NounPhrase(target, features=target._features)
        context.referents[target] = (False, result)
        get_log().error('GRE for "{}" failed : "{}"'.format(target, msg))
        get_log().error('\tusing expr: "{}"'.format(result))
    return result

def _do_repeated_reference(referent, context):
    result = None

    is_unique, re = context.referents[referent]
    if is_unique:
        result = deepcopy(re)
        result.spec = Word('the', 'DETERMINER')
    else:
        result = re
        if not result.has_feature('PROPER', 'true'):
            result.spec = Word('a', 'DETERMINER')
    return result

def _count_type_instances(entity_type, object_map):
    count = 0
    for k, v in object_map.items():
        if v == entity_type: count += 1
    return count


########## new version of REG #############

def optimise_ref_exp(phrase, context):
    """Replace anaphoric noun phrases with pronouns when possible. """
    # TODO: include Number in the dicision process (it vs they)
    # FIXME: Coordinated elements need some special attention
    result = copy(phrase)
    # test for selecting phrases taht can be processed
    test = lambda x: isinstance(x, NounPhrase) or isinstance(x, Coordination)
    # reverse so that we start with large phrases first (eg CC)
    print('-='*40)
    print(list(phrase.constituents()))
    # TODO: reveresed generates cataphora but not reversing skips over coordinations
#    nps = reversed([x for x in phrase.constituents() if test(x)])
    nps = [x for x in phrase.constituents() if test(x)]
    pps = [x for x in phrase.constituents()
                if isinstance(x, PrepositionalPhrase)]
    uttered = []
    processed_ids = set()
    for np in nps:
        get_log().debug('current NP: {}'.format(np))
        gender = get_phrase_gender(np)
        get_log().debug('gender of NP: {}'.format(gender))
        distractors = [x for x in (context.referent_stack + uttered)
            if get_phrase_gender(x) == gender]
#        get_log().debug('distractors of NP:\n\t{}'.format(distractors))
        if id(np) in processed_ids:
            get_log().debug('current NP: {} was already processed'.format(np))
            continue
        if ((np in context.referent_stack or np in uttered)
            and np == distractors[-1]):
            # this np is the most salient so prnoominalise it
            if isinstance(phrase, Clause):
                if id(np) == id(phrase.subj):
                    pronoun = pronominalise(np, gender, PronounUse.subjective)
                elif (np in phrase.subj.constituents() and
                      np in phrase.vp.constituents()):
                    pronoun = pronominalise(np, gender, PronounUse.reflexive)
#                elif any(id(np) in [id(x) for x in pp.constituents()]
#                            for pp in pps):
#                    pronoun = pronominalise(np, gender, PronounUse.possessive)
                elif (np in phrase.vp.constituents()):
                    pronoun = pronominalise(np, gender, PronounUse.objective)
                else:
                    pronoun = pronominalise(np, gender, PronounUse.subjective)
            else:
                pronoun = pronominalise(np, gender, PronounUse.subjective)
            replace_element_with_id(result, id(np), pronoun)
            # if you replace an element, remove all the subphrases from the list
        processed = [y for y in np.constituents()]
        processed_ids.update([id(x) for x in processed])
        uttered.append(np)
#        optimise_determiner(np, distractors, context)
    context.add_sentence(phrase)
    return result


def optimise_determiner(phrase, distractors, context):
    """Select the approrpiate determiner. """
    if (not isinstance(phrase, NounPhrase)):
        return phrase

    if (phrase.has_feature('PROPER', 'true') or
        phrase.head.has_feature('cat', 'PRONOUN')):
            phrase.spec = Element()

    elif (distractors and distractors[-1] == phrase and
          not phrase.head.has_feature('cat', 'PRONOUN')):
              phrase.head.spec = Word('the', 'DETERMINER')
        
    elif (not phrase.head.has_feature('cat', 'PRONOUN')):
          if phrase.head.string[0] in "aeiouy":
              phrase.head.spec = Word('an', 'DETERMINER')
          else:
              phrase.head.spec = Word('a', 'DETERMINER')

    return phrase


def pronominalise(np, *features):
    """Create a pronoun for the corresponding noun phrase. """
    # features can be: person, gender, subject|object (case),
    #   possessive determiner, possessive pronoun, reflexive
    tmp = [x for x in features if str(Gender) == x[0]]
    if len(tmp) == 1:
        gender = tmp[0]
    else:
        gender = get_phrase_gender(np)
    all_features = list(features)
    if gender == Gender.epicene:
        all_features.append(Number.plural)
    else:
        all_features.append(gender)
    all_features.extend(list(np._features.items()))
    get_log().debug('Phrase features for pronominalisation:\n\t{}'
                    .format(all_features))
    res = lexicon.pronoun_for_features(*all_features)
    get_log().debug('\tresult:{}'.format(res))
    return res


def get_phrase_gender(phrase):
    if isinstance(phrase, Coordination):
        return Gender.epicene
    if phrase.has_feature(str(Gender)):
        gender_val = phrase.get_feature(str(Gender))
    elif phrase.head.has_feature(str(Gender)):
        gender_val = phrase.head.get_feature(str(Gender))
    else:
        gender_val = lexicon.guess_noun_gender(str(phrase.head))[1]
    return (str(Gender), gender_val) # FIXME: terrible syntax!

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
