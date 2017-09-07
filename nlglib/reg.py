import re
import logging

from copy import deepcopy, copy

from nlglib.structures import *
from nlglib.microplanning import replace_element, replace_element_with_id
from nlglib import lexicon
from nlglib.lexicon import Person, Case, Number, Gender, Features, PronounUse
from nlglib.lexicon import Pronoun, POS_NOUN
from .globals import current_linguistic_context

logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_log():
    return logging.getLogger(__name__)


def generate_re(msg, **kwargs):
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
        return generate_re_element(msg, **kwargs)
    elif isinstance(msg, Message):
        return generate_re_message(msg, **kwargs)
    elif isinstance(msg, Document):
        return generate_re_document(msg, **kwargs)
    else:
        raise TypeError('"%s" has a wrong type (%s).' %
                        (msg, str(type(msg))))


def generate_re_element(element, **kwargs):
    get_log().debug('Generating RE for element.')
    with_refexp = deepcopy(element)
    _replace_vars_with_nps(with_refexp, **kwargs)
    result = optimise_ref_exp(with_refexp, **kwargs)
    return result


def generate_re_message(msg, **kwargs):
    get_log().debug('Generating RE for message.')
    if msg is None: return None
    nuclei = [generate_re(x, **kwargs) for x in msg.nuclei if x is not None]
    satellite = generate_re(msg.satellite, **kwargs)
    return Message(msg.relation, *nuclei, satellite=satellite)


def generate_re_document(doc, **kwargs):
    """ Iterate through a Document and replace all Vars by
    referring expressions.

    """
    get_log().debug('Generating RE for document.')
    if doc is None: return None
    title = generate_re(doc.title, **kwargs)
    sections = [generate_re(x, **kwargs)
                for x in doc.sections if x is not None]
    return Document(title, *sections)


def _replace_vars_with_nps(message, **kwargs):
    get_log().debug('Replacing vars.')
    for arg in message.arguments():
        ref = arg.value or arg.id
        refexp = generate_ref_exp(ref, **kwargs)
        replace_element(message, arg, refexp)


def generate_ref_exp(referent, **kwargs):
    get_log().debug('GRE for "{0}"'.format(referent))
    context = current_linguistic_context
    if not (isinstance(referent, String) or isinstance(referent, Word)):
        return referent
    if referent in context.referents:
        result = _do_repeated_reference(referent, **kwargs)
    else:
        result = _do_initial_reference(referent, **kwargs)
    return result


def _do_initial_reference(target, **kwargs):
    context = current_linguistic_context
    # do we have information about the referent?
    try:
        onto = context.ontology
        if onto is None:
            get_log().error('GRE does not have ontology!')

        referent = target.string
        # if referent starts with a capital, assume that it is a proper name
        if referent[0].isupper():
            result = NounPhrase(target, features=target.features)
            result.set_feature('PROPER', 'true')
            return result

        entity_type = onto.best_entity_type(':' + referent)
        entity_type = entity_type.rpartition(':')[2]  # strip the ':' at the beginning
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
        result = NounPhrase(target, features=target.features)
        context.referents[target] = (False, result)
    except Exception as msg:
        get_log().exception(msg)
        # if we have no info, assume referent is not unique
        result = NounPhrase(target, features=target.features)
        context.referents[target] = (False, result)
        get_log().error('GRE for "{}" failed : "{}"'.format(target, msg))
        get_log().error('\tusing expr: "{}"'.format(result))
    return result


def _do_repeated_reference(referent, **kwargs):
    context = current_linguistic_context

    is_unique, refexp = context.referents[referent]
    if is_unique:
        result = deepcopy(refexp)
        result.spec = Word('the', 'DETERMINER')
    else:
        result = refexp
        if not result.has_feature('PROPER', 'true'):
            result.spec = Word('a', 'DETERMINER')
    return result


def _count_type_instances(entity_type, object_map):
    count = 0
    for k, v in object_map.items():
        if v == entity_type:
            count += 1
    return count


# ######## new version of REG ############ #

def optimise_ref_exp(phrase, **kwargs):
    """Replace anaphoric noun phrases with pronouns when possible. """
    # TODO: include Number in the dicision process (it vs they)
    # FIXME: Coordinated elements need some special attention
    result = deepcopy(phrase)
    context = current_linguistic_context
    # test for selecting phrases that can be processed
    test = lambda x: isinstance(x, NounPhrase) or isinstance(x, Coordination)
    # reverse so that we start with large phrases first (eg CC)
    get_log().debug('-=' * 40)
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
        if 'PERSON' not in np:
            if context.is_last_speaker(np):
                person = Person.first
            else:
                person = Person.third
        else:
            person = ('PERSON', np['PERSON'])
        phrases = [x for x in (context.np_stack + uttered)
                   if lexicon.guess_phrase_gender(x) == gender]
        #        get_log().debug('distractors of NP:\n\t{}'.format(distractors))
        if id(np) in processed_ids:
            get_log().debug('current NP: {} was already processed'.format(np))
            continue
        # if ((np in context.np_stack or np in uttered) and np == phrases[-1]):
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
            optimise_determiner(np, phrases, **kwargs)
    context.add_sentence(phrase)
    return result


def optimise_determiner(phrase, np_phrases, **kwargs):
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

    if (phrase.has_feature('PROPER', 'true') or
            phrase.has_feature('cat', 'PRONOUN')):
        get_log().debug('...proper or pronoun')
        if not phrase.spec:
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


def pronominalise(np, *features, **kwargs):
    """Create a pronoun for the corresponding noun phrase. """
    # features can be: person, gender, subject|object (case),
    #   possessive determiner, possessive pronoun, reflexive
    get_log().info('Doing pronominalisation on {0}'.format(repr(np)))
    tmp = [x for x in features if str(Gender) == x[0]]
    if len(tmp) == 1:
        gender = tmp[0]
    else:
        gender = lexicon.guess_phrase_gender(np)
    allfeatures = list(features)
    if gender == Gender.epicene:
        allfeatures = [x for x in allfeatures if x != Number.singular]
        allfeatures.append(Number.plural)
    else:
        allfeatures.append(gender)
    allfeatures.extend(list(np.features.items()))
    get_log().debug('Phrase features for pronominalisation:\n\t{}'
                    .format(allfeatures))
    res = lexicon.pronoun_forfeatures(*allfeatures)
    get_log().debug('\tresult:{}'.format(res))
    return res
