# encoding: utf-8

"""Defintion of element classes related to words"""

from __future__ import unicode_literals

from .base import NLGElement
from .string import StringElement
from ..lexicon.feature.lexical import (DEFAULT_INFL, DEFAULT_SPELL, INFLECTIONS,
                                       SPELL_VARS)
from ..lexicon.feature.internal import DISCOURSE_FUNCTION
from ..lexicon.feature.category import (ANY, NOUN, ADJECTIVE, DETERMINER, VERB,
                                        ADVERB, PRONOUN)
from ..util import get_morphology_rules


class WordElement(NLGElement):

    """Element defining rules and behaviour for a word."""

    def __init__(self, base_form=u'', category=u'', id=u'', lexicon=u'',
                 realisation=u''):
        """Create a WordElement with the specified baseForm, category,
        ID and lexicon.

        :param base_form: the base form of WordElement
        :param category: the category of Wor,dElement
        :param id: the ID of word in lexicon
        :param lexicon: the lexicon from witch this WordElement comes from

        """
        super(WordElement, self).__init__(
            category=category, lexicon=lexicon, realisation=realisation)
        self.base_form = base_form
        self.id = id

    def __eq__(self, other):
        if isinstance(other, WordElement):
            return (
                self.base_form == other.base_form
                and self.id == other.id
                and self.features == other.features
            )
        return False

    def __hash__(self):
        return super(WordElement, self).__hash__()

    def __unicode__(self):
        return "<%s [%s:%s]>" % (
            self.__class__.__name__,
            self.base_form,
            self.category if self.category else 'no category')

    @property
    def default_inflection_variant(self):
        return self.features[DEFAULT_INFL]

    @default_inflection_variant.setter
    def default_inflection_variant(self, variant):
        self.features[DEFAULT_INFL] = variant

    @property
    def inflection_variants(self):
        return self.features[INFLECTIONS]

    @inflection_variants.setter
    def inflection_variants(self, variants):
        if not isinstance(variants, list):
            variants = [variants]
        self.features[INFLECTIONS] = variants

    @property
    def spelling_variants(self):
        return self.features[SPELL_VARS]

    @spelling_variants.setter
    def spelling_variants(self, variant):
        self.features[SPELL_VARS] = variant

    @property
    def default_spelling_variant(self):
        default_spelling = self.features.get(DEFAULT_SPELL)
        return self.base_form if default_spelling is None else default_spelling

    @default_spelling_variant.setter
    def default_spelling_variant(self, variant):
        self.features[DEFAULT_SPELL] = variant

    def realise_syntax(self):
        if not self.elided:
            infl = InflectedWordElement(word=self)
            return infl.realise_syntax()

    def realise_morphology(self):
        if self.default_spelling_variant:
            return StringElement(string=self.default_spelling_variant, word=None)

    def inflex(self, category=None, **features):
        """Return an InflectedWordElement holding all argument features."""
        return InflectedWordElement(word=self, category=category, features=features)


class InflectedWordElement(NLGElement):

    """An InflectedWordElement wraps a base WordElement and some features,
    and is in charge of the realisation of the word, given the features.

    Example:
    >>> w = lex.first(u'voiture')
    >>> iw = InflectedWordElement(w, number=PLURAL)
    >>> iw.realise_morphology().realisation
    u'voitures'

    """

    def __init__(self, word, category=None, features=None):
        """Constructs a new inflected word using the argument word as
        the base form.

        Constructing the word also requires a lexical category (such as noun,
        verb).

        :param word: the base form for this inflected word.
        :param category: the lexical category for the word.
        :param features: an optional feature dict

        """
        self.base_word = word
        self.base_form = word.default_spelling_variant
        self.realisation = self.base_form
        self.features = word.features.copy()
        if features:
            self.features.update(features)
        if not category:
            #  the inflected word inherits the base word category
            #  (moved from WordElement.realise_syntax())
            self.category = word.category
        else:
            self.category = ANY

    def __unicode__(self):
        return u"<%s [%s:%s]>" % (
            self.__class__.__name__,
            self.base_form,
            self.category if self.category else u'no category')

    @property
    def parent(self):
        return self.base_word.parent

    @parent.setter
    def parent(self, value):
        self.base_word.parent = value

    @property
    def lexicon(self):
        return self.base_word.lexicon

    def realise_syntax(self):
        if not self.elided and self.lexicon and self.base_form:
            if not self.base_word:
                self.base_word = self.lexicon.first(
                    self.base_form, category=self.category)
        return self

    def realise_morphology(self):
        """Apply morphology rules to update the word realisation
        according to its features.

        """
        if self.non_morph:
            realised_element = StringElement(string=self.base_form, word=self)
            realised_element.features[
                DISCOURSE_FUNCTION] = self.features[DISCOURSE_FUNCTION]
        else:
            if self.base_form:
                base_word = self.base_word
            else:
                base_word = self.lexicon.first(self.base_form)
            rules = get_morphology_rules(self.language)()
            if self.category == NOUN:
                realised_element = rules.morph_noun(self, base_word)
            elif self.category == ADJECTIVE:
                realised_element = rules.morph_adjective(self, base_word)
            elif self.category == DETERMINER:
                realised_element = rules.morph_determiner(self)
            elif self.category == VERB:
                realised_element = rules.morph_verb(self, base_word)
            elif self.category == ADVERB:
                realised_element = rules.morph_adverb(self, base_word)
            elif self.category == PRONOUN:
                realised_element = rules.morph_adverb(self)
        return realised_element
