from pynlg.spec.phrase import (
    StringElement, WordElement,
    PhraseElement, NounPhraseElement, AdjectivePhraseElement,
)
from pynlg.lexicon.feature import category
from pynlg.lexicon.en import EnglishLexicon

from nlglib import logger
from nlglib.features import category as lex_cat
from nlglib import structures

from nlglib.structures import Element, MsgSpec, Message, Document

DEFAULT_LEXICON = EnglishLexicon()


def realise(msg, **kwargs):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, str):
        return msg
    elif isinstance(msg, Element):
        return realise_element(msg, **kwargs)
    elif isinstance(msg, MsgSpec):
        return realise_message_spec(msg, **kwargs)
    elif isinstance(msg, (list, tuple)):
        return realise_list(msg, **kwargs)
    elif isinstance(msg, Message):
        return realise_message(msg, **kwargs)
    elif isinstance(msg, Document):
        return realise_document(msg, **kwargs)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance' %
                        type(msg))


def realise_element(elt, **kwargs):
    """ Realise NLG element. """
    logger.debug('Realising element (simple realisation):\n{0}'
                 .format(repr(elt)))
    lexicon = kwargs.get('lexicon', DEFAULT_LEXICON)
    element = nlglib_to_pynlg(elt, lexicon)
    return element.realise()


def realise_message_spec(msg, **kwargs):
    """ Realise message specification - this should not happen """
    logger.debug('Realising message spec:\n{0}'.format(repr(msg)))
    return realise_element(StringElement(str(msg).strip()), **kwargs)


def realise_list(elt, **kwargs):
    """ Realise a list. """
    logger.debug('Realising list of elements:\n{0}'.format(repr(elt)))
    return ' '.join(realise(x, **kwargs) for x in elt)


def realise_message(msg, **kwargs):
    """ Return a copy of Message with strings. """
    logger.debug('Realising message:\n{0}'.format(repr(msg)))
    if msg is None: return None
    sat = realise(msg.satellite, **kwargs)
    nuclei = [realise(x, **kwargs) for x in msg.nuclei if x is not None]
    #    if len(sats) > 0:
    #        sats[0].add_front_modifier(Word(msg.marker, 'ADV'))
    sentences = _flatten(nuclei + [sat])
    logger.debug('flattened sentences: %s' % sentences)
    # TODO: this si wrong because the recursive call can apply capitalisation
    # and punctuation multiple times...
    sentences = list(map(lambda e: e[:1].upper() + e[1:] +
                                   ('.' if e[-1] != '.' else ''),
                         [s for s in sentences if s != '']))
    return sentences


def realise_document(msg, **kwargs):
    """ Return a copy of a Document with strings. """
    logger.debug('Realising document.')
    if msg is None:
        return None
    title = realise(msg.title, **kwargs)
    sections = [realise(x, **kwargs) for x in msg.sections]
    return Document(title, *sections)


def _flatten(lst):
    """ Return a list where all elemts are items. 
    Any encountered list will be expanded.

    """
    result = list()
    for x in lst:
        if isinstance(x, list):
            for y in x:
                result.append(y)
        else:
            if x is not None:
                result.append(x)
    return result


def pos_to_category(pos):
    mappings = {
        lex_cat.ANY: category.ANY,
        lex_cat.ADJECTIVE: category.ADJECTIVE,
        lex_cat.ADVERB: category.ADVERB,
        lex_cat.AUXILIARY: category.AUXILIARY,
        lex_cat.COMPLEMENTISER: category.COMPLEMENTISER,
        lex_cat.CONJUNCTION: category.CONJUNCTION,
        lex_cat.DETERMINER: category.DETERMINER,
        lex_cat.INTERJECTION: category.CANNED_TEXT,
        lex_cat.MODAL: category.MODAL,
        lex_cat.NOUN: category.NOUN,
        lex_cat.NUMERAL: category.NOUN,
        lex_cat.PARTICLE: category.CANNED_TEXT,
        lex_cat.PREPOSITION: category.PREPOSITION,
        lex_cat.PRONOUN: category.PRONOUN,
        lex_cat.SYMBOL: category.SYMBOL,
        lex_cat.VERB: category.VERB,
    }
    return mappings.get(pos, category.ANY)


def type_to_category(t):
    mappings = {
        structures.NOUN_PHRASE: category.NOUN_PHRASE,
        structures.VERB_PHRASE: category.VERB_PHRASE,
        structures.PREPOSITION_PHRASE: category.PREPOSITIONAL_PHRASE,
        structures.ADJECTIVE_PHRASE: category.ADJECTIVE_PHRASE,
        structures.ADVERB_PHRASE: category.ADVERB_PHRASE,
    }
    return mappings.get(t, category.ANY)


def nlglib_to_pynlg(element, lexicon):
    if element == Element() or element is None:
        return None
    if element.type == structures.STRING:
        return StringElement(element.string, language=lexicon.language)
    if element.type == structures.VAR:
        return StringElement(str(element), language=lexicon.language)
    if element.type == structures.WORD:
        return WordElement(element.word, category=pos_to_category(element.pos), lexicon=lexicon)
    if element.type == structures.CLAUSE:
        p = PhraseElement(lexicon=lexicon, category=category.CLAUSE)
        p.subjects = [nlglib_to_pynlg(element.subj, lexicon)]
        p.verb_phrase = nlglib_to_pynlg(element.vp, lexicon)
        for m in element.front_modifiers:
            p.add_pre_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.premodifiers:
            p.add_pre_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.postmodifiers:
            p.add_post_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.complements:
            p.add_post_complement(nlglib_to_pynlg(m, lexicon))
        return p
    if element.type == structures.NOUN_PHRASE:
        p = NounPhraseElement(lexicon=lexicon)
        p.specifier = nlglib_to_pynlg(element.spec, lexicon)
        p.head = nlglib_to_pynlg(element.head, lexicon)
        for m in element.premodifiers:
            p.add_pre_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.postmodifiers:
            p.add_post_modifier(nlglib_to_pynlg(m, lexicon))
        return p
    if element.type in (structures.VERB_PHRASE,
                        structures.ADJECTIVE_PHRASE,
                        structures.ADVERB_PHRASE,
                        structures.PREPOSITION_PHRASE):
        cat = type_to_category(element.type)
        p = PhraseElement(lexicon=lexicon, category=cat)
        p.head = nlglib_to_pynlg(element.head, lexicon)
        for m in element.premodifiers:
            p.add_pre_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.postmodifiers:
            p.add_post_modifier(nlglib_to_pynlg(m, lexicon))
        for m in element.complements:
            p.add_complement(nlglib_to_pynlg(m, lexicon))
        return p
