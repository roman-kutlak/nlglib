# encoding: utf-8

"""Definition of the lexicon handlers."""

import os
import pkg_resources
import random

from copy import deepcopy
from collections import defaultdict
from xml.etree import cElementTree as ElementTree

from .feature.category import ANY
from nlglib.exc import UnhandledLanguage
from nlglib.spec.word import WordElement

__all__ = ['Lexicon']


class Lexicon(object):

    """A Lexicon is a collection of metadata about words of a specific language. """

    #  node names in lexicon XML files
    BASE = "base"

    #  base form of Word
    CATEGORY = "category"

    #  base form of Word
    ID = "id"

    #  base form of Word
    WORD = "word"

    #  node defining a word
    #  inflectional codes which need to be set as part of INFLECTION feature
    INFL_CODES = [
        "reg", "irreg", "uncount", "inv",
        "metareg", "glreg", "nonCount", "sing", "groupuncount"]

    language = None

    def __init__(self, auto_index=True):
        """Create a new Lexicon.

        If auto_index is set to True, the XML lexicon corresponding to
        the argument language will be parsed, and several indexes will
        be built at instanciation.

        :param auto_index: whether to parse index the lexicon data at
                           instanciation (default: True)

        """
        self.tree = None
        self.words = set()
        self.id_index = {}
        self.base_index = defaultdict(list)
        self.variant_index = defaultdict(list)
        self.category_index = defaultdict(list)

        if auto_index:
            self.make_indexes()

    def __contains__(self, word_feature):
        return bool(self.get(word_feature, create_if_missing=False))

    def __getitem__(self, word_feature):
        return self.get(word_feature, category=ANY)

    def __repr__(self):
        return '<%s - %s (%s)>' % (
            self.__class__.__name__,
            self.language,
            'indexed' if self.indexed else 'unindexed')

    @property
    def indexed(self):
        return bool(self.id_index)

    def create_word(self, word):
        self.words.add(word)
        self.index_word(word)

    def get(self, word_feature, category=ANY, create_if_missing=True):
        """Fetch the WordElement(s) associated to the argument word
        feature (an, a base form etc) from the Lexicon indexes.

        If the word is not found, create it if the argument
        ``create_if_missing`` is set to True. Else, return None.

        """
        # Search by base form
        if self.base_index.get(word_feature):
            word = self.indexed_words_by_category(
                word_feature, category, self.base_index)
        # Search by variant
        elif self.variant_index.get(word_feature):
            word = self.indexed_words_by_category(
                word_feature, category, self.variant_index)
        # Search by id
        elif self.id_index.get(word_feature):
            word = [self.indexed_words_by_category(
                word_feature, category, self.id_index)]
        elif create_if_missing:
            word = WordElement(
                base_form=word_feature, category=category, id=None,
                lexicon=self, realisation=word_feature)
            self.create_word(word)
        else:
            return
        # don't return the indexed word, but return a deepcopy, so that
        # any modification to the returned word won't impact the index
        if isinstance(word, list):
            return [deepcopy(w) for w in word]
        else:
            return deepcopy(word)

    def first(self, word_feature, category=ANY):
        """Return the first matching word identified by the word_feature
        in one of the Lexicon indexes.

        """
        matches = self.get(word_feature, category=category)
        if isinstance(matches, WordElement):
            return matches
        elif isinstance(matches, list):
            return matches[0] if matches else None

    def indexed_words_by_category(self, word_feature, category, index):
        if category == ANY:
            return index[word_feature]
        else:
            return [w for w in index[word_feature] if w.category == category]

    def parse_xml_lexicon(self):
        return ElementTree.parse(self.lexicon_filepath)

    def make_indexes(self):
        """Parse the appropriate XML lexicon, and build several indexes,
        allowing fast access using several facets (id, word, base,
        variant, category).

        """
        self.tree = self.parse_xml_lexicon()
        root = self.tree.getroot()
        for word_node in root:
            word = self.word_from_node(word_node)
            if word:
                self.create_word(word)

    def word_from_node(self, word_node):
        """Convert a word node of the lexicon to a WordElement."""
        if word_node.tag != self.WORD:
            return None
        word = WordElement(base_form=None, category=None, id=None, lexicon=self)
        inflections = []
        for feature_node in word_node:
            feature_name = str(feature_node.tag.strip())
            feature_value = feature_node.text
            assert bool(feature_name), "empty feature_name for word_node %s" % (
                feature_value)
            if feature_value is not None:
                feature_value = str(feature_value.strip())

            # Set word base_form, id, category, inflection codes and features
            if feature_name == self.BASE:
                word.base_form = feature_value
                word.realisation = feature_value
            elif feature_name == self.ID:
                word.id = feature_value
            elif feature_name == self.CATEGORY:
                word.category = feature_value.upper()
            elif not feature_value:
                if feature_name in self.INFL_CODES:
                    inflections.append(feature_name)
                else:
                    word[feature_name] = True
            else:
                word[feature_name] = feature_value

        # If no inflection is specified, assume the word is regular
        inflections = inflections or ['reg']

        # The default inflection code is "reg" if we have it, else we take
        # random pick from the available inflection codes
        if 'reg' in inflections:
            default_inflection = 'reg'
        else:
            default_inflection = random.choice(inflections)

        # Set inflection information on word
        word.default_inflection_variant = default_inflection
        word.inflection_variants = inflections

        return word

    def index_word(self, word):
        if word.base_form:
            self.base_index[word.base_form].append(word)
            self.variant_index[word.base_form].append(word)
        if word.id is not None:
            if word.id in self.id_index:
                raise ValueError('Index %s already in id_index' % word.id)
            else:
                self.id_index[word.id] = word
        if word.category is not None:
            self.category_index[word.category].append(word)

    @property
    def lexicon_filepath(self):
        """Return the path to the XML lexicon file associated with the
        instance language.

        """
        lexicon_name = 'package_data/%s-lexicon.xml' % self.language
        filepath = pkg_resources.resource_filename('nlglib', lexicon_name)

        if not os.path.exists(filepath):
            raise UnhandledLanguage(
                '%s language is not handled: %s file not found.' % (
                    self.language, filepath))
        return filepath

    @staticmethod
    def is_dict_subset(d1, d2):
        s1 = {(k, tuple(v) if isinstance(v, list) else v) for k, v in d1.items()}
        s2 = {(k, tuple(v) if isinstance(v, list) else v) for k, v in d2.items() if k in d1}
        return s1 == s2

    def find_by_features(self, features, category=ANY):
        """Return the first word found with features including the
        argument features, and having the same category as the argument
        one.

        """
        haystack = self.words if category == ANY else self.category_index[category]
        for word in haystack:
            if self.is_dict_subset(features, word.features):
                return word

    def find_all_by_features(self, features, category=ANY):
        """Return all words found with features including the
        argument features, and having the same category as the argument
        one.

        """
        haystack = self.words if category == ANY else self.category_index[category]
        for word in haystack:
            if self.is_dict_subset(features, word.features):
                yield word
