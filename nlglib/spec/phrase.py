# encoding: utf-8

"""Definition of the PhraseElement class and associated subclasses:

- NounPhraseElement
- AdjectivePhraseElement
- VerbPhraseElement
- ClausePhraseElement

"""

from .base import NLGElement
from .string import StringElement
from .word import WordElement
from nlglib.util import get_phrase_helper
from nlglib.lexicon import feature
from nlglib.lexicon.feature import ELIDED, NUMBER, form, tense
from nlglib.lexicon.feature import category as cat
from nlglib.lexicon.feature import internal
from nlglib.lexicon.feature import clause
from nlglib.lexicon.feature import discourse
from nlglib.lexicon.feature import person
from nlglib.lexicon.feature import number

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
        # copy head features to the phrase
        self['gender'] = head.gender
        self['acronym'] = head.acronym
        self['number'] = head.number
        self['person'] = head.person
        self['possessive'] = head.possessive
        self['passive'] = head.passive
        self['discourse_function'] = head.discourse_function

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

    def set_features_from_element(self, element):
        self.possessive = element.possessive


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
    such as pre_modifiers.

    """

    def __init__(self, lexicon):
        super(AdjectivePhraseElement, self).__init__(
            category=cat.ADJECTIVE_PHRASE, lexicon=lexicon)

    @property
    def adjective(self):
        return self.head

    @adjective.setter
    def adjective(self, adjective):
        if isinstance(adjective, str):
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


class VerbPhraseElement(PhraseElement):
    """This class defines a verb phrase
    
    It is essentially a wrapper around the <code>PhraseElement</code> class,
    with methods for setting common constituents such as Objects.
    For example, the <code>setVerb</code> method in this class sets
    the head of the element to be the specified verb
    <p>
    From an API perspective, this class is a simplified version of the SPhraseSpec
    class in simplenlg V3.  It provides an alternative way for creating syntactic
    structures, compared to directly manipulating a V4 <code>PhraseElement</code>.
    <p>
    Methods are provided for setting and getting the following constituents:
    <UL>
    <LI>PreModifier		(eg, "reluctantly")
    <LI>Verb			(eg, "gave")
    <LI>IndirectObject	(eg, "Mary")
    <LI>Object	        (eg, "an apple")
    <LI>PostModifier    (eg, "before school")
    </UL>
    <p>
    NOTE: If there is a complex verb group, a preModifer set at the VP level appears before
    the verb, while a preModifier set at the clause level appears before the verb group.  Eg
    "Mary unfortunately will eat the apple"  ("unfortunately" is clause preModifier)
    "Mary will happily eat the apple"  ("happily" is VP preModifier)
    <p>
    NOTE: The setModifier method will attempt to automatically determine whether
    a modifier should be expressed as a PreModifier or PostModifier
    <p>
    Features (such as negated) must be accessed via the <code>setFeature</code> and
    <code>getFeature</code> methods (inherited from <code>NLGElement</code>).
    Features which are often set on VPPhraseSpec include
    <UL>
    <LI>Modal    (eg, "John eats an apple" vs "John can eat an apple")
    <LI>Negated  (eg, "John eats an apple" vs "John does not eat an apple")
    <LI>Passive  (eg, "John eats an apple" vs "An apple is eaten by John")
    <LI>Perfect  (eg, "John ate an apple" vs "John has eaten an apple")
    <LI>Progressive  (eg, "John eats an apple" vs "John is eating an apple")
    <LI>tense    (eg, "John ate" vs "John eats" vs "John will eat")
    </UL>
    Note that most VP features can be set on an SPhraseSpec, they will automatically
    be propagated to the VP
    
    <code>VPPhraseSpec</code> are produced by the <code>createVerbPhrase</code>
    method of a <code>PhraseFactory</code>

    """

    def __init__(self, lexicon, phrase=None):
        super().__init__(category=cat.VERB_PHRASE, lexicon=lexicon)
        self.helper = get_phrase_helper(
            language=self.lexicon.language,
            phrase_type=cat.VERB_PHRASE)()
        if phrase:
            self.features.update(phrase.features)
            self.parent = phrase.parent

        # set default feature values
        self.features[feature.PERFECT] = False
        self.features[feature.PROGRESSIVE] = False
        self.features[feature.PASSIVE] = False
        self.features[feature.NEGATED] = False
        self.features[feature.TENSE] = tense.PRESENT
        self.features[feature.PERSON] = person.THIRD
        self.features[feature.NUMBER] = number.SINGULAR
        self.features[feature.FORM] = form.NORMAL
        self.features[internal.REALISE_AUXILIARY] = True

    @property
    def verb(self):
        return self.head

    @verb.setter
    def verb(self, verb):
        """Sets the verb (head) of a verb phrase; extract particle from verb if necessary"""
        if isinstance(verb, str):  # if String given, check for particle
            space = verb.find(" ")

            if space == -1:  # no space, so no particle
                verb_element = self.lexicon.first(verb, category=cat.VERB)

            else:  # space, so break up into verb and particle
                verb, _, particle = verb.partition(" ")
                verb_element = self.lexicon.first(verb, category=cat.VERB)
                self.features[feature.PARTICLE] = particle

        else:  # Object is not a String
            verb_element = verb

        self.features[internal.HEAD] = verb_element

    @property
    def object(self):
        """Return the direct object of a clause (assumes there is only one)"""
        for complement in self.complements:
            if complement.discourse_function == discourse.OBJECT:
                return complement
        return None

    @object.setter
    def object(self, direct_object):
        """Set the direct object of a clause (assumes this is the only direct object)"""
        if not direct_object:
            return
        if (
                direct_object.category == cat.CLAUSE
                # TODO: define CoordinatedPhraseElement
                # or isinstance(direct_object, CoordinatedPhraseElement)
        ):
            object_phrase = direct_object
        else:
            object_phrase = NounPhraseElement(self.lexicon)
            object_phrase.head = direct_object

        object_phrase.features[internal.DISCOURSE_FUNCTION] = discourse.OBJECT
        self.add_complement(object_phrase)

    @property
    def indirect_object(self):
        """Returns the indirect object of a clause (assumes there is only one)"""
        for complement in self.complements:
            if complement.discourse_function == discourse.INDIRECT_OBJECT:
                return complement
        return None

    @indirect_object.setter
    def indirect_object(self, indirect_object):
        """Set the indirect object of a clause (assumes this is the only direct indirect object)"""
        if not indirect_object:
            return
        if (
                indirect_object.category == cat.CLAUSE
                # TODO: define CoordinatedPhraseElement
                # or isinstance(direct_object, CoordinatedPhraseElement)
        ):
            object_phrase = indirect_object
        else:
            object_phrase = NounPhraseElement(self.lexicon)
            object_phrase.head = indirect_object

        object_phrase.features[internal.DISCOURSE_FUNCTION] = discourse.INDIRECT_OBJECT
        self.add_complement(object_phrase)
    
    # note that addFrontModifier, addPostModifier, addPreModifier are inherited from PhraseElement
    # likewise getFrontModifiers, getPostModifiers, getPreModifiers

    # Add a modifier to a verb phrase
    # Use heuristics to decide where it goes
    #
    # @param modifier
    #/
    # @Override
    # public void addModifier(Object modifier):
    #     # adverb is preModifier
    #     # string which is one lexicographic word is looked up in lexicon,
    #     # if it is an adverb than it becomes a preModifier
    #     # Everything else is postModifier
    #
    #     if (modifier is None)
    #         return
    #
    #     # get modifier as NLGElement if possible
    #     NLGElement modifierElement = null
    #     if (modifier instanceof NLGElement)
    #         modifierElement = (NLGElement) modifier
    #     else if (modifier instanceof String):
    #         String modifierString = (String) modifier
    #         if (modifierString.length() > 0 and !modifierString.contains(" "))
    #             modifierElement = getFactory().createWord(modifier, LexicalCategory.ANY)
    #
    #
    #     # if no modifier element, must be a complex string
    #     if (modifierElement is None):
    #         addPostModifier((String) modifier)
    #         return
    #
    #
    #     # extract WordElement if modifier is a single word
    #     WordElement modifierWord = null
    #     if (modifierElement is not None and modifierElement instanceof WordElement)
    #         modifierWord = (WordElement) modifierElement
    #     else if (modifierElement is not None and modifierElement instanceof InflectedWordElement)
    #         modifierWord = ((InflectedWordElement) modifierElement).getBaseWord()
    #
    #     if (modifierWord is not None and modifierWord.getCategory() == LexicalCategory.ADVERB):
    #         addPreModifier(modifierWord)
    #         return
    #
    #
    #     # default case
    #     addPostModifier(modifierElement)


def make_noun_phrase(lexicon, specifier, noun, modifiers=None):
    phrase = NounPhraseElement(lexicon)
    phrase.head = noun
    phrase.specifier = specifier
    if modifiers:
        if not isinstance(modifiers, list):
            modifiers = [modifiers]
        for modifier in modifiers:
            phrase.add_modifier(modifier)
    return phrase
