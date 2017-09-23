# encoding: utf-8
""" This module serves as a simple lexicon. It allows the user to create
word elements of the appropriate category easily.

"""

import six
import random

from copy import deepcopy
from collections import defaultdict
from xml.etree import cElementTree as ElementTree
from os.path import join, dirname, abspath, exists
import sys
import logging
import pkg_resources
import xml.etree.ElementTree as ET
from collections import defaultdict
from copy import deepcopy
from pickle import load

from nlglib.structures import Word

from ..features.category import *
from .name_genders import name_genders

logger = logging.getLogger(__name__)

__all__ = ['Lexicon', 'brown_tag_to_standard_tag', 'brown_tag_tofeatures',
           'guess_noun_gender', 'guess_phrase_gender', 'guess_phrase_number']

_sentinel = object()


class Lexicon(object):
    """ A class that represents a lexicon. """

    tag_map = {
        '': ANY,
        'adj': ADJECTIVE,
        'adjective': ADJECTIVE,
        'adv': ADVERB,
        'adverb': ADVERB,
        'aux': AUXILIARY,
        'auxiliary': AUXILIARY,
        'compl': COMPLEMENTISER,
        'complement': COMPLEMENTISER,
        'conj': CONJUNCTION,
        'conjunction': CONJUNCTION,
        'det': DETERMINER,
        'determiner': DETERMINER,
        'interjection': INTERJECTION,
        'modal': MODAL,
        'noun': NOUN,
        'num': NUMERAL,
        'numeral': NUMERAL,
        'particle': PARTICLE,
        'prep': PREPOSITION,
        'preposition': PREPOSITION,
        'pron': PRONOUN,
        'pronoun': PRONOUN,
        'sym': SYMBOL,
        'symbol': SYMBOL,
        'verb': VERB,
    }

    def __init__(self):
        # dict of all words (base_form -> [Word])
        self.words = defaultdict(list)
        # functions called when LexiconContext is exited
        self.teardown_lexicon_context_funcs = []
        # setup tagger if supported:
        try:
            tagger_name = 'resources/averaged_perceptron_tagger.pickle'
            tagger_path = pkg_resources.resource_filename('nlglib', tagger_name)
            with open(tagger_path, 'rb') as tagger:
                self.tagger = load(tagger)
        except FileNotFoundError:
            logger.error('Could not load pickled tagger.')
            self.tagger = None

    @classmethod
    def from_xml(cls, path):
        """ Create a new instance of a Lexicon from the NIH lexicon in XML. """
        lexicon = cls()
        tree = ET.parse(path)
        lex_records = tree.getroot()
        for lex_record in lex_records:
            word = cls.parse_node(lex_record)
            if word:
                lexicon.insert_word(word)
        return lexicon

    @classmethod
    def parse_node(cls, lex_record):
        tag = lex_record.find('base')
        if tag is not None:
            word = tag.text
        else:
            return None
        tag = lex_record.find('category')
        if tag is not None:
            pos = cls.tag_map.get(tag.text, ANY)
        else:
            pos = ANY
        id = lex_record.find('id')
        if id is not None:
            id = id.text
        w = Word(word, pos, id=id)
        return w

    def insert_word(self, word):
        """ Insert a word into the lexicon. """
        self.words[word.word].append(word)

    def first(self, base_form, pos=ANY):
        return self.get(base_form, pos, create=False)

    def get(self, base_form, pos=ANY, create=True):
        words = self.filter(base_form, pos)
        if words:
            return words[0]
        if create:
            word = Word(base_form, pos)
            self.words[base_form].append(word)
            return deepcopy(word)
        return None

    def filter(self, base_form, pos=ANY):
        """Return words corresponding to base form and optionally POS tag."""
        words = self.words[base_form]
        rv = [deepcopy(w) for w in words if pos == ANY or w.pos == pos]
        return rv

    def __getattr__(self, attr):
        """Return a word with given category if `attr` is POS or raise `AttributeError`

        If a dict is passed as a second argument, update the word's features with the dict.

        >>> self.noun('house')
        Word('house', 'NOUN', {'cat': 'NOUN'})
        >>> self.noun('house', {'NUMBER': 'plural'})
        Word('house', 'NOUN', {'NUMBER': 'plural', 'cat': 'NOUN'})
        >>> self.foo('house')
        AttributeError: Lexicon does not have attribute foo

        """
        if attr.upper() in TAGS:
            def fn(wordform, features=None):
                rv = self.get(wordform, attr.upper())
                rv.features.update(features or {})
                return rv
            return fn
        else:
            cls_name = self.__class__.__name__
            raise AttributeError('{} does not have attribute {}'.format(cls_name, attr))

    def do_teardown_lexicon_context(self, exc=_sentinel):
        """Called when a pipeline context is popped. """
        if exc is _sentinel:
            exc = sys.exc_info()[1]
        for func in reversed(self.teardown_lexicon_context_funcs):
            func(exc)


def brown_tag_tofeatures(tag):
    """ Return the features corresponding to the given (Brown corp) tag. """
    features = {}
    if tag.endswith('$'):
        features['POSSESSIVE'] = 'true'
        if not tag.startswith('PrepositionPhrase'):
            features['CASE'] = 'GENITIVE'
    if tag.endswith('*'): features['NEGATED'] = 'true'
    if tag.startswith('NP'): features['PROPER'] = 'true'
    if tag.startswith('NNS'): features['NUMBER'] = 'PLURAL'
    if tag.startswith('NPS'): features['NUMBER'] = 'PLURAL'
    if tag.startswith('JJR'): features['COMPARATIVE'] = 'true'
    if tag.startswith('JJS'): features['SUPERLATIVE'] = 'true'
    if tag.startswith('JJT'): features['SUPERLATIVE'] = 'true'
    if tag.startswith('VB'): features['BASE_FORM'] = 'true'
    if tag.startswith('VBD'): features['TENSE'] = 'PAST'
    if tag.startswith('VBG'): features['TENSE'] = 'PRESENT_PARTICIPLE'
    if tag.startswith('VBN'): features['TENSE'] = 'PAST_PARTICIPLE'
    if tag.startswith('VBP'): features['TENSE'] = 'PRESENT'
    if tag.startswith('VBZ'): features['TENSE'] = 'PRESENT3S'
    # TODO: implement the rest of the table...
    #   http://www.scs.leeds.ac.uk/ccalas/tagsets/brown.html
    return features


def brown_tag_to_standard_tag(tag):
    """ Map a Brown corpus tag to one of the TAGS.
    If the tag is not in the lookup table, return SYMBOL.
    The function simplifies most combinations of tags eg.
    MD+HV = modal auxillary + verb "to have" as in "shouldda" -> MODAL.

    """
    if tag.startswith('A'): return DETERMINER
    if tag.startswith('B'): return VERB  # be, is, was, isn't, ...
    if tag == 'CC' or tag == 'CS': return CONJUNCTION
    if tag.startswith('CD'): return NUMERAL
    if tag.startswith('DO'): return VERB  # do, did, didn't, ...
    if tag.startswith('DT'): return DETERMINER
    if tag.startswith('EX'): return ADVERB  # existential 'there'
    # ignore foreign words -- use the attached tag (FW-JJ -> JJ)
    if tag.startswith('FW-'): return brown_tag_to_standard_tag(tag[3:])
    if tag.startswith('HV'): return VERB  # has, had, didn't have, ...
    if tag.startswith('IN'): return PREPOSITION
    if tag.startswith('J'): return ADJECTIVE
    if tag.startswith('MD'): return MODAL
    if tag.startswith('N'): return NOUN
    if tag.startswith('OD'): return NUMERAL
    if tag.startswith('PN'): return PRONOUN
    if tag.startswith('PP'): return PRONOUN
    if tag.startswith('Q'): return DETERMINER
    if tag.startswith('R'): return ADVERB
    if tag.startswith('TO'): return VERB
    if tag.startswith('V'): return VERB
    if tag.startswith('WDT'): return DETERMINER
    if tag.startswith('WP'): return PRONOUN
    if tag.startswith('WQ'): return ADVERB
    if tag.startswith('WR'): return ADVERB
    # unknown tag?
    return SYMBOL


def guess_noun_gender(word):
    """Guess the gender of the given word. """
    from nlglib.features import gender
    key = word.upper()
    if key.upper() in name_genders:
        val = name_genders[key]
        if val == 'male':
            return gender.MASCULINE
        elif val == 'female':
            return gender.FEMININE
        else:
            return gender.EPICENE
    # if we don't know, return neuter
    return gender.NEUTER


def guess_phrase_gender(phrase):
    from nlglib.structures import Coordination
    from nlglib.features import gender
    if isinstance(phrase, Coordination):
        return gender.EPICENE
    if 'GENDER' in phrase:
        gender_val = phrase['GENDER']
    elif 'GENDER' in phrase.head:
        gender_val = phrase.head['GENDER']
    else:
        gender_val = guess_noun_gender(str(phrase.head))[1]
    return gender_val


def guess_phrase_number(phrase):
    """Guess the gender of the given phrase. """
    from nlglib.structures import Phrase, Coordination
    from nlglib.features import number
    if 'NUMBER' in phrase:
        return 'NUMBER', phrase['NUMBER']
    if isinstance(phrase, Phrase) and 'NUMBER' in phrase.head:
        return 'NUMBER', phrase.head['NUMBER']
    if isinstance(phrase, Coordination):
        return number.PLURAL
    return number.SINGULAR
