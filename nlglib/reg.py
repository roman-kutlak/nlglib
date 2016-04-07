
import re
from copy import deepcopy, copy
import logging

from .structures import Clause, Coordination, Document, Element, Message
from .structures import MsgSpec, NounPhrase, Paragraph
from .structures import PrepositionalPhrase, Section, String, Word
from .microplanning import replace_element, replace_element_with_id
from . import lexicon
from .lexicon import Person, Case, Number, Gender, Features, PronounUse
from .lexicon import Pronoun, POS_NOUN


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


class Context:
    def __init__(self, ontology=None):
        self.ontology = ontology
        self.referents = dict()
        self.referent_stack = []
        self.np_stack = []
        self.history = []
        self.rfexps = []
        # this can be used for direct speach or system/user customisation
        self.speakers = []
        self.hearers = []

    def is_speaker(self, element):
        """Return True if the element is a speaker. """
        return element in self.speakers

    def is_last_speaker(self, element):
        """Return True if the element is the current (last) speaker. """
        return element in self.speakers[-1:]

    def add_speaker(self, element):
        """Add the `element` to the list of speakers as the last speaker. """
        self.speakers.append(element)

    def remove_speaker(self, element):
        """Delete the `element` from the list of speakers. """
        self.speakers.remove(element)

    def remove_last_speaker(self):
        """If there are any speakers, remove the last one and return it. """
        if self.speakers:
            return self.speakers.pop()

    def is_hearer(self, element):
        """Return True if the given elemen is a hearer. """
        return element in self.hearers

    def is_last_hearer(self, element):
        """Return True if the given elemen is the current (last) hearer. """
        return element in self.hearers[:-1]

    def add_hearer(self, element):
        """Add the `element` to the list of hearers as the last hearer. """
        self.hearers.append(element)

    def remove_hearer(self, element):
        """Delete the `element` from the list of hearers. """
        self.hearers.remove(element)

    def remove_last_hearer(self):
        """If there are any hearers, remove the last one and return it. """
        if self.hearers:
            return self.hearers.pop()

    def add_sentence(self, sent):
        """Add a sentence to the context. """
        self.history.append(sent)
        # add potential referents/distractors
        self._update_referents(sent)

    def _update_referents(self, sent):
        """Extract NPs and add them on the referent stack. Add subject last. """
        nps = [x for x in sent.constituents()
                   if isinstance(x, NounPhrase) or
                      (isinstance(x, Coordination) and
                       isinstance(x.coords[0], NounPhrase))]
        for np in nps:
            nouns = [x for x in np.constituents()
                        if (isinstance(x, Word) and x.pos == POS_NOUN)]
            self.referent_stack.extend(reversed(nouns))
            unspec_np = deepcopy(np)
            unspec_np.spec = Element()
            self.np_stack.append(unspec_np)

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


######### new version of REG #############

def optimise_ref_exp(phrase, context):
    """Replace anaphoric noun phrases with pronouns when possible. """
    # TODO: include Number in the dicision process (it vs they)
    # FIXME: Coordinated elements need some special attention
    result = copy(phrase)
    # test for selecting phrases taht can be processed
    test = lambda x: isinstance(x, NounPhrase) or isinstance(x, Coordination)
    # reverse so that we start with large phrases first (eg CC)
    get_log().debug('-='*40)
    get_log().debug('constituents:')
    for x in phrase.constituents():
        get_log().debug('\t {}'.format(' '.join(repr(x).split())))
    nps = [x for x in phrase.constituents() if test(x)]
    uttered = []
    processed_ids = set()
    for np in nps:
        replaced = False
        get_log().debug('current NP:\n{}'.format(np))
        gender = lexicon.guess_phrase_gender(np)
        get_log().debug('gender of NP: {}'.format(gender))
        number = lexicon.guess_phrase_number(np)
        get_log().debug('number of NP: {}'.format(number))
        if not np.has_feature('PERSON'):
            if context.is_last_speaker(np):
                person = Person.first
            else:
                person = Person.third
        else:
            person = ('PERSON', np.get_feature('PERSON'))
        phrases = [x for x in (context.np_stack + uttered)
            if lexicon.guess_phrase_gender(x) == gender]
#        get_log().debug('distractors of NP:\n\t{}'.format(distractors))
        if id(np) in processed_ids:
            get_log().debug('current NP: {} was already processed'.format(np))
            continue
#        if ((np in context.np_stack or np in uttered) and np == phrases[-1]):
        if (np in phrases[-1:]):
            # this np is the most salient so pronominalise it
            if isinstance(phrase, Clause):
                if id(np) == id(phrase.subj):
                    pronoun = pronominalise(np, gender, PronounUse.subjective, person)
                elif (np in phrase.subj.constituents() and
                      np in phrase.vp.constituents()):
                    pronoun = pronominalise(np, gender, PronounUse.reflexive, person)
                # TODO: implement -- possessive will be used if it is a complement of an NP?
#                elif any(id(np) in [id(x) for x in pp.constituents()]
#                            for pp in pps):
#                    pronoun = pronominalise(np, gender, PronounUse.possessive)
                elif (np in phrase.vp.constituents()):
                    pronoun = pronominalise(np, gender, PronounUse.objective, person)
                else:
                    pronoun = pronominalise(np, gender, PronounUse.subjective, person)
            else:
                pronoun = pronominalise(np, gender, PronounUse.subjective, person)
            get_log().debug('replacing {}:{} with {}'.format(id(np), np, pronoun))
            replace_element_with_id(result, id(np), pronoun)
            replaced = True
        # if you replace an element, remove all the subphrases from the list
        processed = [y for y in np.constituents()]
        processed_ids.update([id(x) for x in processed])
        unspec_np = deepcopy(np)
        unspec_np.spec = Element()
        uttered.append(unspec_np)
        if not replaced:
            # fix determiners in the processed NP
            optimise_determiner(np, phrases, context)
    context.add_sentence(phrase)
    return result


def optimise_determiner(phrase, np_phrases, context):
    """Select the approrpiate determiner. """
    get_log().debug('Fixing determiners: {}'.format(phrase))
    if (not isinstance(phrase, NounPhrase)):
        get_log().debug('...not an NP')
        return phrase

    get_log().debug('NPs: {}'
        .format(' '.join([str(x) for x in np_phrases])))

    # FIXME: this whould look at all modifiers
    distractors = [x for x in np_phrases
                    if (hasattr(x, 'head') and
                        hasattr(phrase, 'head') and phrase.head == x.head)]
    get_log().debug('distractors: {}'
        .format(' '.join([str(x) for x in distractors])))

    if (phrase.head.has_feature('PROPER', 'true') or
        phrase.head.has_feature('cat', 'PRONOUN')):
            get_log().debug('...proper or pronoun')
            phrase.spec = Element()

    elif (not phrase.head.has_feature('cat', 'PRONOUN') and
              phrase in distractors[-1:] and
              len(distractors) == 1):
          get_log().debug('...unpronominalised phrase that is last mentioned')
          phrase.spec = Word('the', 'DETERMINER')

    elif (lexicon.guess_phrase_number(phrase) != Number.plural and
              not phrase.head.has_feature('cat', 'PRONOUN')):
          get_log().debug('...indefinite')
          if phrase.head.string and phrase.head.string[0] in "aeiouy":
              phrase.spec = Word('an', 'DETERMINER')
          else:
              phrase.spec = Word('a', 'DETERMINER')
    return phrase


def pronominalise(np, *features):
    """Create a pronoun for the corresponding noun phrase. """
    # features can be: person, gender, subject|object (case),
    #   possessive determiner, possessive pronoun, reflexive
    get_log().info('Doing pronominalisation on {0}'.format(repr(np)))
    tmp = [x for x in features if str(Gender) == x[0]]
    if len(tmp) == 1:
        gender = tmp[0]
    else:
        gender = lexicon.guess_phrase_gender(np)
    all_features = list(features)
    if gender == Gender.epicene:
        all_features = [x for x in all_features if x != Number.singular]
        all_features.append(Number.plural)
    else:
        all_features.append(gender)
    all_features.extend(list(np._features.items()))
    get_log().debug('Phrase features for pronominalisation:\n\t{}'
                    .format(all_features))
    res = lexicon.pronoun_for_features(*all_features)
    get_log().debug('\tresult:{}'.format(res))
    return res



############################################################################
#
# Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
# All rights reserved.
#
# This file is part of SAsSy NLG library.
#
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of University of Aberdeen nor
#     the names of its contributors may be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
#
############################################################################
