# encoding: utf-8

"""Definition of the PhraseElement class and associated subclasses:

- NounPhraseElement
- AdjectivePhraseElement
- VerbPhraseElement
- ClausePhraseElement

"""

import six

from .base import NLGElement
from .string import StringElement
from .word import WordElement
from ..util import get_phrase_helper
from ..lexicon.feature import ELIDED, NUMBER
from ..lexicon.feature import category as cat
from ..lexicon.feature import internal
from ..lexicon.feature import clause
from ..lexicon.feature import discourse


__all__ = ['PhraseElement', 'AdjectivePhraseElement', 'NounPhraseElement']


class PhraseElement(NLGElement):

    def __init__(self, lexicon, category):
        """Create a phrase of the given type."""
        super(PhraseElement, self).__init__(category=category, lexicon=lexicon)
        self.features[ELIDED] = False
        self.helper = get_phrase_helper(language=self.lexicon.language,
                                        phrase_type='phrase')()
        self.features[internal.COMPLEMENTS] = []

    @property
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        if isinstance(value, NLGElement):
            head = value
        else:
            head = StringElement(string=value)
        head.parent = self
        self.features[internal.HEAD] = head

    def get_children(self):
        """Return the child components of the phrase.

        The returned list will depend of the category of the element:
        - Clauses consist of cue phrases, front modifiers, pre-modifiers
        subjects, verb phrases and complements.
        - Noun phrases consist of the specifier, pre-modifiers, the noun
        subjects, complements and post-modifiers.
        - Verb phrases consist of pre-modifiers, the verb group,
        complements and post-modifiers.
        - Canned text phrases have no children.
        - All other phrases consist of pre-modifiers, the main phrase
        element, complements and post-modifiers.

        """
        children = []
        if self.category == cat.CLAUSE:
            children.append(self.cue_phrase or [])
            children.extend(self.front_modifiers or [])
            children.extend(self.premodifiers or [])
            children.extend(self.subjects or [])
            children.extend(self.verb_phrase or [])
            children.extend(self.complements or [])
        elif self.category == cat.NOUN_PHRASE:
            children.append(self.specifier or [])
            children.extend(self.premodifiers or [])
            children.append(self.head or [])
            children.extend(self.complements or [])
            children.extend(self.postmodifiers or [])
        elif self.category == cat.VERB_PHRASE:
            children.extend(self.premodifiers or [])
            children.append(self.head or [])
            children.extend(self.complements or [])
            children.extend(self.postmodifiers or [])
        else:
            children.extend(self.premodifiers or [])
            children.append(self.head or [])
            children.extend(self.complements or [])
            children.extend(self.postmodifiers or [])

        children = (child for child in children if child)
        children = [
            StringElement(string=child)
            if not isinstance(child, NLGElement) else child
            for child in children]
        return children

    def add_complement(self, complement):
        """Adds a new complement to the phrase element.

        Complements will be realised in the syntax after the head
        element of the phrase. Complements differ from post-modifiers
        in that complements are crucial to the understanding of a phrase
        whereas post-modifiers are optional.

        If the new complement being added is a clause or a
        CoordinatedPhraseElement then its clause status feature is set
        to ClauseStatus.SUBORDINATE and it's discourse function is set
        to DiscourseFunction.OBJECT by default unless an existing
        discourse function exists on the complement.

        """
        complements = self.features.get(internal.COMPLEMENTS, [])
        if (
                complement.category == cat.CLAUSE
                # TODO: define CoordinatedPhraseElement
                # or isinstance(complement, CoordinatedPhraseElement)
        ):
            complement[internal.CLAUSE_STATUS] = clause.SUBORDINATE
            if not complement.discourse_function:
                complement[internal.DISCOURSE_FUNCTION] = discourse.OBJECT

            complement.parent = self
        complements.append(complement)
        self.features[internal.COMPLEMENTS] = complements

    def add_post_modifier(self, new_post_modifier):
        """Add the argument post_modifer as the phrase post modifier,
        and set the parent of the post modifier as the current sentence.

        """
        new_post_modifier.parent = self
        current_post_modifiers = self.postmodifiers or []
        current_post_modifiers.append(new_post_modifier)
        self.postmodifiers = current_post_modifiers

    def add_pre_modifier(self, new_pre_modifier):
        """Add the argument pre_modifer as the phrase pre modifier,
        and set the parent of the pre modifier as the current sentence.

        """
        new_pre_modifier.parent = self
        current_pre_modifiers = self.premodifiers or []
        current_pre_modifiers.append(new_pre_modifier)
        self.premodifiers = current_pre_modifiers

    def realise(self):
        return self.helper.realise(phrase=self)


class AdjectivePhraseElement(PhraseElement):

    """This class defines a adjective phrase.

    It is essentially a wrapper around the
    PhraseElement class, with methods for setting common constituents
    such as premodifiers.

    """

    def __init__(self, lexicon):
        super(AdjectivePhraseElement, self).__init__(
            category=cat.ADJECTIVE_PHRASE, lexicon=lexicon)

    @property
    def adjective(self):
        return self.head

    @adjective.setter
    def adjective(self, adjective):
        if isinstance(adjective, six.text_type):
            # Create a word, if not found in lexicon
            adjective = self.lexicon.first(adjective, category=cat.ADJECTIVE)
        self.features[internal.HEAD] = adjective


class NounPhraseElement(PhraseElement):

    """

    This class defines a noun phrase. It is essentially a wrapper around the
    PhraseElement class, with methods for setting common
    constituents such as specifier. For example, the setNoun method
    in this class sets the head of the element to be the specified noun

    From an API perspective, this class is a simplified version of the
    NPPhraseSpec class in simplenlg V3. It provides an alternative way for
    creating syntactic structures, compared to directly manipulating a V4
    PhraseElement.

    """

    def __init__(self, lexicon, phrase=None):
        super(NounPhraseElement, self).__init__(
            category=cat.NOUN_PHRASE,
            lexicon=lexicon)
        self.helper = get_phrase_helper(
            language=self.lexicon.language,
            phrase_type=cat.NOUN_PHRASE)()
        if phrase:
            self.features.update(phrase.features)
            self.parent = phrase.parent

    @property
    def noun(self):
        return self.head

    @noun.setter
    def noun(self, value):
        self.features[cat.NOUN] = value
        self.features[internal.HEAD] = value

    @property
    def pronoun(self):
        return self.features[cat.PRONOUN]

    @pronoun.setter
    def pronoun(self, value):
        self.features[cat.PRONOUN] = value
        self.features[internal.HEAD] = value

    @property
    def specifier(self):
        return self.features[internal.SPECIFIER]

    @specifier.setter
    def specifier(self, value):
        if value is None:
            return
        if isinstance(value, NLGElement):
            specifier = value
        else:
            specifier = self.lexicon.first(value, category=cat.DETERMINER)

        if specifier:
            specifier.features[internal.DISCOURSE_FUNCTION] = discourse.SPECIFIER
            specifier.parent = self
            if isinstance(self.head, WordElement) and self.head.category == cat.PRONOUN:
                self.noun = self.lexicon.first(self.head.base_form, category=cat.NOUN)
            if specifier.number:
                self.features[NUMBER] = specifier.number

        self.features[internal.SPECIFIER] = specifier

    def add_modifier(self, modifier):
        self.helper.add_modifier(phrase=self, modifier=modifier)

    def check_if_ne_only_negation(self):
        return self.specifier.ne_only_negation or self.head.ne_only_negation
