
from .base import NounPhraseHelper, PhraseHelper
from nlglib.spec.base import NLGElement
from nlglib.spec.list import ListElement
from nlglib.spec.string import StringElement
from nlglib.spec.phrase import AdjectivePhraseElement, PhraseElement, CoordinatedPhraseElement
from nlglib.spec.word import WordElement, InflectedWordElement
from nlglib.lexicon import feature
from nlglib.lexicon.feature import category, discourse, internal, pronoun, gender, number, lexical, person

__all__ = ['EnglishPhraseHelper', 'EnglishNounPhraseHelper']


class EnglishPhraseHelper(PhraseHelper):
    """A syntax defining specific behaviour for English sentences."""


class EnglishNounPhraseHelper(NounPhraseHelper):
    """A syntax defining specific behaviour for English noun phrases."""

    def add_modifier(self, phrase, modifier):
        """Add the argument modifier to the phrase pre/post modifier list.

        """
        if not modifier:
            return
        # string which is one lexicographic word is looked up in lexicon,
        # preposed adjective is preModifier
        # Everything else is postModifier
        if isinstance(modifier, NLGElement):
            modifier_element = modifier
        else:
            modifier_element = phrase.lexicon.get(modifier, create_if_missing=False)
            if modifier_element:
                modifier_element = modifier_element[0]

            # Add word to lexicon
            elif ' ' not in modifier:
                modifier_element = WordElement(
                    base_form=modifier,
                    realisation=modifier,
                    lexicon=phrase.lexicon,
                    category=category.ADJECTIVE)
                phrase.lexicon.create_word(modifier_element)

        # if no modifier element was found, it must be a complex string,
        # add it as postModifier
        if not modifier_element:
            phrase.add_post_modifier(StringElement(string=modifier))
            return
        #  adjective phrase is a premodifer
        elif isinstance(modifier_element, AdjectivePhraseElement):
            head = modifier_element.head
            if head.preposed and not modifier_element.complements:
                phrase.add_pre_modifier(modifier_element)
                return
        # Extract WordElement if modifier is a single word
        else:
            modifier_word = modifier_element
            #  check if modifier is an adjective
            if modifier_word and modifier_word.category == category.ADJECTIVE:
                phrase.add_pre_modifier(modifier_word)
                return
        #  default case
        phrase.add_post_modifier(modifier_element)

    def create_pronoun(self, phrase):
        """Return an InflectedWordElement wrapping a personal pronoun
        corresponding to the phrase features (number, gender and person).

        """
        if phrase.number == number.SINGULAR:
            if phrase.person == person.FIRST:
                word = 'I'
            elif phrase.person == person.SECOND:
                word = 'you'
            else:
                if phrase.gender == gender.FEMININE:
                    word = 'she'
                elif phrase.gender == gender.MASCULINE:
                    word = 'he'
                else:
                    word = 'it'
        elif phrase.number == number.PLURAL:
            if phrase.person == person.FIRST:
                word = 'we'
            elif phrase.person == person.SECOND:
                word = 'you'
            else:
                word = 'they'
        else:
            word = "both"

        new_pronoun_elt = phrase.lexicon.first(word, category=category.PRONOUN)
        new_pronoun_infl_elt = new_pronoun_elt.inflex(
            discourse_function=phrase.discourse_function)
        new_pronoun_infl_elt.gender = phrase.gender
        new_pronoun_infl_elt.person = phrase.person
        new_pronoun_infl_elt.number = phrase.number
        if phrase.discourse_function:
            new_pronoun_infl_elt.discourse_function = phrase.discourse_function
        else:
            new_pronoun_infl_elt.discourse_function = discourse.SPECIFIER
        new_pronoun_infl_elt.possessive = phrase.possessive
        return new_pronoun_infl_elt


class CoordinatedPhraseHelper(PhraseHelper):

    def realise(self, phrase):
        """The main method for realising phrases.

        The following sentence components will be realised:

        - the pre modifiers
        - the coordinates
        - the complements
        - the post modifiers

        Return a ListElement, containing the realised components.

        """
        if not phrase or phrase.elided:
            return None

        realised = ListElement()
        self.realise_list(realised_element=realised,
                          element_list=phrase.premodifiers,
                          discourse_function=discourse.PRE_MODIFIER)
        self.realise_coordinates(phrase=phrase, realised_element=realised)
        self.realise_list(realised_element=realised,
                          element_list=phrase.postmodifiers,
                          discourse_function=discourse.POST_MODIFIER)
        self.realise_complements(phrase=phrase, realised_element=realised)
        return realised

    def realise_coordinates(self, phrase, realised_element):
        """Realises the complements of the phrase."""
        coordinates = phrase.features[internal.COORDINATES] or []
        if not coordinates:
            return

        realisation = ListElement()

        conjunction = phrase.lexicon.first(phrase.conjunction, category=category.CONJUNCTION).inflex(
            discourse_function=discourse.CONJUNCTION
        ) if phrase.conjunction else None

        if phrase.raise_specifier:
            self.raise_specifier(coordinates)

        coordinates[-1].possessive = phrase.possessive
        coordinate = coordinates[0]
        self._set_child_features(coordinate, phrase)
        realisation.append(coordinate.realise())

        for coordinate in coordinates[1:]:
            self._set_child_features(coordinate, phrase)
            if phrase.aggregate_auxiliary:
                coordinate.realise_auxiliary = False

            if coordinate.category == category.CLAUSE:
                coordinate.suppressed_complementiser = phrase.suppressed_complementiser

            element = coordinate.realise()
            if not element:
                continue

            # don't add conjunction if empty
            if conjunction:
                realisation.append(conjunction)
            realisation.append(element)

        # add the entire new cc to the list of realised elements
        realised_element.append(realisation)
        return realised_element

    def raise_specifier(self, children):
        """Check to see if the specifier can be raised and then raises it.

        In order to be raised the specifier must be the same on all coordinates. For
        example, <em>the cat and the dog</em> will be realised as
        <em>the cat and dog</em> while <em>the cat and any dog</em> will remain
        <em>the cat and any dog</em>.

        @param children the `List` of coordinates in the `CoordinatedPhraseElement`
       """
        if not children:
            return

        def get_specifier(element):
            if not element:
                return None
            return element.specifier.base_form

        first = get_specifier(children[0])

        specifiers = [get_specifier(e) for e in children if get_specifier(e)]
        return len(specifiers) == len(children) and all(s == first for s in specifiers)

    @staticmethod
    def _set_child_features(child, phrase):
        child.progressive = phrase.progressive
        child.perfect = phrase.perfect
        child.specifier = phrase.specifier
        child.gender = phrase.gender
        child.number = phrase.number
        child.tense = phrase.tense
        child.person = phrase.person
        child.negated = phrase.negated
        child.modal = phrase.modal
        child.discourse_function = phrase.discourse_function
        child.form = phrase.form
        child.clause_status = phrase.clause_status
        if phrase.interrogative_type:
            child.ignore_modal = True


def get_head_word_element(element):
    """Retrieves the correct representation of the word from the element.

    This method will find the `WordElement`, if it exists, for the
    given phrase or inflected word.

    @param element the `NLGElement` from which the head is required.
    @return the `WordElement`
    """
    if not element:
        return None

    if isinstance(element, WordElement):
        return element
    elif isinstance(element, InflectedWordElement):
        return element.base_word
    elif isinstance(element, PhraseElement):
        return get_head_word_element(element.head)
