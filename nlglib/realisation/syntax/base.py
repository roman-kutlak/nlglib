# encoding: utf-8

"""Definition of generic phrase syntaxes."""


from nlglib.lexicon.feature.discourse import PRE_MODIFIER, SPECIFIER, COMPLEMENT, POST_MODIFIER
from nlglib.lexicon.feature.category import PRONOUN, NOUN_PHRASE
from nlglib.lexicon.feature import NUMBER, IS_COMPARATIVE, IS_SUPERLATIVE
from nlglib.lexicon.feature import internal
from nlglib.lexicon.feature.discourse import HEAD
from nlglib.spec.list import ListElement
from nlglib.spec.word import InflectedWordElement


class PhraseHelper(object):

    """Class providing utility methods related to Phrase objects.

    The PhraseHelper methods are language agnostic. Define any language
    specific method in a PhraseHelper subclass.

    """

    def realise(self, phrase):
        """The main method for realising phrases.

        The following sentence components will be realised:

        - the pre modifiers
        - the head
        - the complements
        - the post modifiers

        Return a ListElement, containing the realised components.

        """
        if not phrase:
            return None

        # `realised` is used as an "output" parameter where functions append to the list inside
        realised = ListElement()
        self.realise_list(realised_element=realised,
                          element_list=phrase.premodifiers,
                          discourse_function=PRE_MODIFIER)
        self.realise_head(phrase=phrase, realised_element=realised)
        self.realise_complements(phrase=phrase, realised_element=realised)
        self.realise_list(realised_element=realised,
                          element_list=phrase.postmodifiers,
                          discourse_function=POST_MODIFIER)
        return realised

    def realise_list(self, realised_element, element_list, discourse_function):
        """Realise each memeber of the element_list and add their
        realisation to the realised_element.

        Each element in the list is to take the argument discourse function.
        If discourse_function is None, then the element discourse function
        is kept unchanged.

        """
        element_list = element_list or []
        for element in element_list:
            element = element.realise_syntax()
            if not element:
                continue
            if discourse_function:
                element.features[internal.DISCOURSE_FUNCTION] = discourse_function
            realised_element.append(element)
        # TODO: this has changed in simplenlg to keep lists together instead of unnesting them as done above
        #  to allow followup components like ortography to make better decisions.

    def realise_head(self, phrase, realised_element):
        """Realise the head of the phrase."""
        head = phrase.head
        if head:
            if phrase.is_comparative:
                head.features[IS_COMPARATIVE] = phrase.is_comparative
            elif phrase.is_superlative:
                head.features[IS_SUPERLATIVE] = phrase.is_superlative
            head = head.realise_syntax()
            head.features[internal.DISCOURSE_FUNCTION] = HEAD
            realised_element.append(head)

    def realise_complements(self, phrase, realised_element):
        """Realises the complements of the phrase."""
        complements = phrase.complements or []
        for i, complement in enumerate(complements):
            element = complement.realise_syntax()
            if not element:
                continue
            element.features[internal.DISCOURSE_FUNCTION] = COMPLEMENT
            if i > 0:
                infl_conjunction_coordination = InflectedWordElement(
                    word=phrase.lexicon.conjunction_coordination)
                realised_element.append(infl_conjunction_coordination)
            realised_element.append(element)

    def is_expletive_subject(self, phrase):
        """Determines if the given phrase has an expletive as a subject."""
        if len(phrase.subjects) == 1:
            subject_np = phrase.subjects[0]
            if subject_np.category == NOUN_PHRASE:
                return bool(subject_np.expletive_subject)
        return False


class NounPhraseHelper(PhraseHelper):

    """Base class for all languages noun phrase helpers."""

    def realise(self, phrase):
        if not phrase or phrase.elided:
            return None

        realised_element = ListElement()
        # Creates the appropriate pronoun if the noun phrase is pronominal.
        if phrase.pronominal:
            realised_element.append(self.create_pronoun(phrase))
        else:
            self.realise_specifier(phrase, realised_element)
            # TODO: add modifier ordering
            phrase.helper.realise_list(realised_element,
                                       element_list=phrase.premodifiers,
                                       discourse_function=PRE_MODIFIER)
            self.realise_head_noun(phrase, realised_element)
            phrase.helper.realise_list(realised_element,
                                       element_list=phrase.complements,
                                       discourse_function=COMPLEMENT)
            phrase.helper.realise_list(realised_element,
                                       element_list=phrase.postmodifiers,
                                       discourse_function=POST_MODIFIER)
        return realised_element

    def realise_head_noun(self, phrase, realised):
        """Realise the head noun of the phrase, and append the result
        to the argument realised list.

        : param realised: the current realised ListElement

        """
        head = phrase.head
        if not head:
            return None
        head = head.realise_syntax()
        # if not isinstance(head, InflectedWordElement):
        #     head = InflectedWordElement(word=head)
        head.gender = phrase.gender
        head.acronym = phrase.acronym
        head.number = phrase.number
        head.person = phrase.person
        head.possessive = phrase.possessive
        head.passive = phrase.passive
        head.discourse_function = phrase.discourse_function
        realised.append(head)

    def realise_specifier(self, phrase, realised):
        """Realise the phrase specifier and add it to the argument
        realised list.

        The specifier will only be realised if the phrase is not raised.

        Note: The RAISED flag can be set when specifiers in a
        coordinated phrase should be raised. For example, the
        coordinated phrase "my cat and my dog" can have its specifiers
        raised becoming "my cat and dog".

        : param realised: the current realised ListElement

        """
        if phrase.specifier and not phrase.raised:
            realised_element = phrase.specifier.realise_syntax()
            realised_element.features[internal.DISCOURSE_FUNCTION] = SPECIFIER
            if phrase.specifier.category == PRONOUN:
                realised_element.features[NUMBER] = phrase.number
            realised.append(realised_element)

    def create_pronoun(self, phrase):
        raise NotImplementedError()
