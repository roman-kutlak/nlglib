# encoding: utf-8

"""Definition of the StringElement class, a container for arbitrary
strings, with unknown category and features.

"""

from .base import NLGElement
from ..lexicon.feature import ELIDED
from ..lexicon.feature.category import CANNED_TEXT
from ..lexicon.lang import DEFAULT as DEFAULT_LANG
from ..util import get_lexicon, get_morphophonology_rules


class StringElement(NLGElement):

    """Generic container for a word with undefined category and features.

    A StringElement can either wrap a word (eg: a WordElement), or a
    simple string. In the latter case, the StringElement category is
    set to 'CANNED_TEXT', a special category used for arbitrary text.

    """

    def __init__(self, string=None, word=None, language=DEFAULT_LANG):
        self.features = {}
        self.features[ELIDED] = False
        self.lexicon = get_lexicon(language)
        self.children = []
        self.parent = None
        if not word:
            self.category = CANNED_TEXT
            self.realisation = string
        else:
            self.features.update(word.features.copy())
            self.category = word.category
            self.realisation = string if string else word.realisation

    def __unicode__(self):
        return u"<%s [%s:%s]>" % (
            self.__class__.__name__,
            self.realisation,
            self.category if self.category else u'no category')

    def __eq__(self, other):
        return (
            isinstance(other, StringElement)
            and super(StringElement, self).__eq__(other)
            and self.realisation == other.realisation
        )

    def realise_morphophonology(self, next_word):
        ruleset = get_morphophonology_rules(self.language)
        ruleset(left_word=self, right_word=next_word)
