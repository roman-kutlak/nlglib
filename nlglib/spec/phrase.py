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
from nlglib.lexicon.feature import lexical
from nlglib.lexicon.feature import person
from nlglib.lexicon.feature import number
from nlglib.lexicon.feature import gender

__all__ = [
    "CoordinatedPhraseElement",
    "PhraseElement",
    "AdjectivePhraseElement",
    "AdverbPhraseElement",
    "NounPhraseElement",
    "PrepositionPhraseElement",
    "VerbPhraseElement",
    "Clause",
]


_sentinel = object()

VP_FEATURES = (
    feature.MODAL,
    feature.TENSE,
    feature.NEGATED,
    feature.NUMBER,
    feature.PASSIVE,
    feature.PERFECT,
    feature.PARTICLE,
    feature.PERSON,
    feature.PROGRESSIVE,
    feature.FORM,
    feature.INTERROGATIVE_TYPE,
    internal.REALISE_AUXILIARY,
)


class CoordinatedPhraseElement(NLGElement):

    PLURAL_COORDINATORS = ["and"]

    def __init__(self, *coordinates, lexicon=None):
        super().__init__(lexicon=lexicon)
        self.features[ELIDED] = False
        self.features[discourse.CONJUNCTION] = "and"
        for c in coordinates:
            self.add_coordinate(c)
        self.helper = get_phrase_helper(language=self.lexicon.language,
                                        phrase_type=cat.COORDINATED_PHRASE)()

    def add_coordinate(self, element):
        """Adds a new coordinate to the phrase element.

        If the new coordinate is a
        `NLGElement` then it is added directly to the coordination. If
        the new coordinate is a string a `StringElement`
        is created and added to the coordination. `StringElement`s
        will have their complementisers suppressed by default. In the case of
        clauses, complementisers will be suppressed if the clause is not the
        first element in the coordination.

        """
        coordinates = self.features.get(internal.COORDINATES, [])
        if isinstance(element, str):
            element = StringElement(string=element, lexicon=self.lexicon)
            element.features[feature.SUPPRESSED_COMPLEMENTISER] = True
        else:
            if element.category == cat.CLAUSE and len(coordinates) > 0:
                element.features[feature.SUPPRESSED_COMPLEMENTISER] = True
        element.parent = self
        coordinates.append(element)
        self.features[internal.COORDINATES] = coordinates

    def get_children(self):
        """Return the child components of the coordinated phrase.

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
        children.extend(self.premodifiers or [])
        children.append(self.coordinates or [])
        children.extend(self.complements or [])
        children.extend(self.postmodifiers or [])

        children = (child for child in children if child)
        children = [
            StringElement(string=child)
            if not isinstance(child, NLGElement) else child
            for child in children]
        return children

    def add_pre_modifier(self, new_pre_modifier):
        """Add the argument pre_modifer as the phrase pre modifier,
        and set the parent of the pre modifier as the current sentence.

        """
        if isinstance(new_pre_modifier, str):
            new_pre_modifier = StringElement(new_pre_modifier, lexicon=self.lexicon)
        new_pre_modifier.parent = self
        current_pre_modifiers = self.premodifiers or []
        current_pre_modifiers.append(new_pre_modifier)
        self.premodifiers = current_pre_modifiers

    def add_post_modifier(self, new_post_modifier):
        """Add the argument post_modifer as the phrase post modifier,
        and set the parent of the post modifier as the current sentence.

        """
        if isinstance(new_post_modifier, str):
            new_post_modifier = StringElement(new_post_modifier, lexicon=self.lexicon)
        new_post_modifier.parent = self
        current_post_modifiers = self.postmodifiers or []
        current_post_modifiers.append(new_post_modifier)
        self.postmodifiers = current_post_modifiers

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
        if isinstance(complement, str):
            complement = StringElement(complement, lexicon=self.lexicon)
        complement.parent = self
        complements = self.features.get(internal.COMPLEMENTS, [])
        complements.append(complement)
        self.features[internal.COMPLEMENTS] = complements

    def get_last_coordinate(self):
        children = self.get_children()
        if children:
            return children[-1]
        return None

    def realise(self):
        return self.helper.realise(phrase=self)


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
        self.set_features_from_element(head)

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
        if not element:
            return

        self.set_feature_from_element(element, feature.IS_COMPARATIVE)
        self.set_feature_from_element(element, feature.POSSESSIVE)
        self.set_feature_from_element(element, feature.NUMBER, default_value=number.SINGULAR)
        self.set_feature_from_element(element, feature.PERSON, default_value=person.THIRD)
        self.set_feature_from_element(element, feature.lexical.GENDER, default_value=gender.NEUTER)
        self.set_feature_from_element(element, feature.lexical.EXPLETIVE_SUBJECT)

    def set_feature_from_element(self, element, feature_name, default_value=_sentinel, reset=False):
        value = getattr(element, feature_name, default_value)
        if value is not _sentinel:
            self.features[feature_name] = value
        if reset:
            self.features.pop(feature_name, None)

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
        if isinstance(new_pre_modifier, str):
            new_pre_modifier = StringElement(new_pre_modifier, lexicon=self.lexicon)
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
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        self.adjective = value

    @property
    def adjective(self):
        return self.head

    @adjective.setter
    def adjective(self, adjective):
        if isinstance(adjective, str):
            # Create a word, if not found in lexicon
            adjective = self.lexicon.first(adjective, category=cat.ADJECTIVE)
        adjective.parent = self
        self.features[internal.HEAD] = adjective
        self.set_features_from_element(adjective)

    def set_features_from_element(self, element):
        if not element:
            return

        self.set_feature_from_element(element, feature.IS_COMPARATIVE)
        self.set_feature_from_element(element, feature.IS_SUPERLATIVE)


class AdverbPhraseElement(PhraseElement):
    """This class defines an adverb phrase.

    It is essentially a wrapper around the
    PhraseElement class, with methods for setting common constituents
    such as pre_modifiers.

    """

    def __init__(self, lexicon):
        super(AdverbPhraseElement, self).__init__(
            category=cat.ADVERB_PHRASE, lexicon=lexicon)

    @property
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        self.adverb = value

    @property
    def adverb(self):
        return self.head

    @adverb.setter
    def adverb(self, adverb):
        if isinstance(adverb, str):
            adverb = self.lexicon.first(adverb, category=cat.ADVERB)
        adverb.parent = self
        self.features[internal.HEAD] = adverb
        self.set_features_from_element(adverb)

    def set_features_from_element(self, element):
        if not element:
            return

        self.set_feature_from_element(element, feature.IS_COMPARATIVE)
        self.set_feature_from_element(element, feature.IS_SUPERLATIVE)


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
        self.features[internal.SPECIFIER] = None

    @property
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        self.noun = value

    @property
    def noun(self):
        return self.head

    @noun.setter
    def noun(self, value):
        if isinstance(value, str):
            value = self.lexicon.first(value, category=cat.NOUN)
        value.parent = self
        self.features[cat.NOUN] = value
        self.features[internal.HEAD] = value

    @property
    def pronoun(self):
        return self.features[cat.PRONOUN]

    @pronoun.setter
    def pronoun(self, value):
        if isinstance(value, str):
            value = self.lexicon.first(value, category=cat.PRONOUN)
        value.parent = self
        self.features[cat.PRONOUN] = value
        self.features[internal.HEAD] = value

    @property
    def specifier(self):
        return self.features[internal.SPECIFIER]

    @specifier.setter
    def specifier(self, value):
        if value is None:
            self.features[internal.SPECIFIER] = None
            return

        if isinstance(value, str):
            specifier = self.lexicon.first(value, category=cat.DETERMINER)
        else:
            specifier = value

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


class PrepositionPhraseElement(PhraseElement):
    """This class defines a preposition phrase.

    It is essentially a wrapper around the
    PhraseElement class, with methods for setting common constituents
    such as pre_modifiers.

    """

    def __init__(self, lexicon):
        super(PrepositionPhraseElement, self).__init__(
            category=cat.PREPOSITIONAL_PHRASE, lexicon=lexicon)

    @property
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        self.preposition = value

    @property
    def preposition(self):
        return self.head

    @preposition.setter
    def preposition(self, preposition):
        if isinstance(preposition, str):
            # Create a word, if not found in lexicon
            preposition = self.lexicon.first(preposition, category=cat.PREPOSITION)
        preposition.parent = self
        self.features[internal.HEAD] = preposition


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
    def head(self):
        return self.features.get(internal.HEAD)

    @head.setter
    def head(self, value):
        self.verb = value

    @property
    def verb(self):
        return self.head

    @verb.setter
    def verb(self, verb):
        """Sets the verb (head) of a verb phrase; extract particle from verb if necessary"""
        if isinstance(verb, str):  # if String given, check for particle
            if " " not in verb:  # no space, so no particle
                verb_element = self.lexicon.first(verb, category=cat.VERB)
            else:  # space, so break up into verb and particle
                verb, _, particle = verb.partition(" ")
                verb_element = self.lexicon.first(verb, category=cat.VERB)
                self.features[feature.PARTICLE] = particle
        elif not isinstance(verb, NLGElement):
            raise ValueError('Unknown verb type')
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
        if isinstance(direct_object, (PhraseElement, CoordinatedPhraseElement)):
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


class Clause(PhraseElement):
    """Clause - sentence.
    From simplenlg:

    * FrontModifier (eg, "Yesterday")
    * Subject (eg, "John")
    * PreModifier (eg, "reluctantly")
    * Verb (eg, "gave")
    * IndirectObject (eg, "Mary")
    * Object (eg, "an apple")
    * PostModifier (eg, "before school")

    Note that verb, indirect object, and object
    are propagated to the underlying verb phrase

    """

    def __init__(self, lexicon=None):
        super().__init__(lexicon=lexicon, category=cat.CLAUSE)
        self.helper = get_phrase_helper(language=self.lexicon.language,
                                        phrase_type=cat.CLAUSE)()
        self.features[ELIDED] = False
        self.features[internal.CLAUSE_STATUS] = clause.MATRIX
        self.features[feature.SUPPRESSED_COMPLEMENTISER] = False
        self.features[lexical.EXPLETIVE_SUBJECT] = False
        self.features[feature.COMPLEMENTISER] = lexicon.first("that", cat.COMPLEMENTISER)

    def __setitem__(self, feature_name, feature_value):
        """Set the feature name/value in the element feature dict."""
        self.features[feature_name] = feature_value
        if self.verb_phrase and isinstance(self.verb_phrase, VerbPhraseElement):
            # propagate relevant features to the VP
            if feature_name in VP_FEATURES:
                self.verb_phrase[feature_name] = feature_value

    def __delitem__(self, feature_name):
        """Remove the argument feature name and its associated value from
        the element feature dict.

        If the feature name was not initially present in the feature dict,
        a KeyError will be raised.

        """
        if feature_name in self.features:
            del self.features[feature_name]
            if (self.verb_phrase and
                    isinstance(self.verb_phrase, VerbPhraseElement) and
                    feature_name in self.verb_phrase):
                del self.verb_phrase[feature_name]


def to_word(lexicon, string, category=cat.ANY):
    if not isinstance(string, NLGElement):
        return lexicon.first(str(string), category)
    return string


def make_adjective_phrase(lexicon, adjective, modifiers=None):
    phrase = AdjectivePhraseElement(lexicon)
    phrase.adjective = to_word(lexicon, adjective, cat.ADJECTIVE)
    if modifiers:
        if not isinstance(modifiers, list):
            modifiers = [modifiers]
        for modifier in modifiers:
            phrase.add_modifier(modifier)
    return phrase


def make_noun_phrase(lexicon, specifier, noun, modifiers=None):
    phrase = NounPhraseElement(lexicon)
    phrase.head = to_word(lexicon, noun, cat.NOUN)
    phrase.specifier = to_word(lexicon, specifier, cat.DETERMINER)
    if modifiers:
        if not isinstance(modifiers, list):
            modifiers = [modifiers]
        for modifier in modifiers:
            phrase.add_modifier(to_word(lexicon, modifier, cat.ADJECTIVE))
    return phrase


def make_verb_phrase(lexicon, verb, complements=None):
    phrase = VerbPhraseElement(lexicon)
    phrase.verb = to_word(lexicon, verb, cat.VERB)
    if complements:
        if not isinstance(complements, list):
            complements = [complements]
        for complement in complements:
            phrase.add_complement(to_word(lexicon, complement))
    return phrase
