# encoding: utf-8

"""Definition of french helpers related to sentence syntax."""


from .base import NounPhraseHelper, PhraseHelper
from nlglib.spec.base import NLGElement
from nlglib.spec.word import WordElement
from nlglib.spec.string import StringElement
from nlglib.spec.list import ListElement
from nlglib.spec.phrase import AdjectivePhraseElement, NounPhraseElement
from nlglib.lexicon.feature.category import PRONOUN, ADJECTIVE, DETERMINER, COMPLEMENTISER
from nlglib.lexicon.feature import PERSON, NUMBER
from nlglib.lexicon.feature.lexical import GENDER
from nlglib.lexicon.feature.person import THIRD
from nlglib.lexicon.feature.gender import MASCULINE
from nlglib.lexicon.feature.number import SINGULAR
from nlglib.lexicon.feature.lexical import PRONOUN_TYPE
from nlglib.lexicon.feature.internal.fr import RELATIVISED
from nlglib.lexicon.feature.pronoun import PERSONAL
from nlglib.lexicon.feature.internal import DISCOURSE_FUNCTION
from nlglib.lexicon.feature.discourse import SPECIFIER


__all__ = ['FrenchPhraseHelper', 'FrenchNounPhraseHelper']


class FrenchPhraseHelper(PhraseHelper):

    """A syntax defining specific behaviour for french sentences."""

    def realise(self, phrase):
        if phrase:
            if not phrase.realivised:
                return super(FrenchPhraseHelper, self).realise(phrase)
            else:
                del phrase[RELATIVISED]


class FrenchNounPhraseHelper(NounPhraseHelper):

    @staticmethod
    def is_ordinal(element):
        """Recognises ordinal adjectives by their ending ("ième").

        Exceptions : "premier", "second" and "dernier" are treated in
        the lexicon.

        """
        if not element:
            return False
        if isinstance(element, StringElement):
            base_form = element.realisation
        else:
            base_form = element.base_form
        return base_form and base_form.endswith('ième')

    def create_pronoun(self, phrase):
        """Return an InflectedWordElement wrapping a personal pronoun
        corresponding to the phrase features (number, gender and person).

        """
        features = {
            PRONOUN_TYPE: PERSONAL,
            PERSON: phrase.person or THIRD,  # default person is third
            NUMBER: phrase.number or SINGULAR,  # default number is singular
            # POSSESSIVE: bool(phrase.possessive)
            # I commented out this guy because a pronoun cannot be possessive...
        }
        # Only check gender feature for third person pronouns
        if features[PERSON] == THIRD:
            # default gender for third person pronouns is masculine
            features[GENDER] = phrase.gender or MASCULINE

        new_pronoun_elt = (
            phrase.lexicon.find_by_features(features, category=PRONOUN)
            or phrase.lexicon.first('il', category=PRONOUN))
        new_pronoun_infl_elt = new_pronoun_elt.inflex(
            discourse_function=phrase.discourse_function,
            passive=phrase.passive)
        return new_pronoun_infl_elt

    def add_modifier(self, phrase, modifier):
        """Add the argument modifier to the phrase pre/post modifier
        list.

        """
        if not modifier:
            return
        # string which is one lexicographic word is looked up in lexicon,
        # preposed adjective is preModifier
        # Everything else is postModifier
        modifier_element = None
        if isinstance(modifier, NLGElement):
            modifier_element = modifier
        else:
            modifier_element = phrase.lexicon.get(modifier, create_if_missing=False)
            if modifier_element:
                modifier_element = modifier_element[0]

            # Add word to lexicon
            if (
                not modifier_element
                and (
                    self.is_ordinal(modifier_element)
                    or (modifier and ' ' not in modifier)
                )
            ):
                modifier_element = WordElement(
                    base_form=modifier,
                    realisation=modifier,
                    lexicon=phrase.lexicon,
                    category=ADJECTIVE)
                phrase.lexicon.create_word(modifier_element)

        # if no modifier element was found, it must be a complex string,
        # add it as postModifier
        if not modifier_element:
            phrase.add_post_modifier(StringElement(string=modifier))
            return
        #  adjective phrase is a premodifer
        elif isinstance(modifier_element, AdjectivePhraseElement):
            head = modifier_element.head
            if (
                (head.preposed or self.is_ordinal(head))
                and not modifier_element.complements
            ):
                phrase.add_pre_modifier(modifier_element)
                return
        # Extract WordElement if modifier is a single word
        else:
            modifier_word = modifier_element
            #  check if modifier is an adjective
            if (
                    modifier_word
                    and modifier_word.category == ADJECTIVE
                    and modifier_element.preposed
                    or self.is_ordinal(modifier_word)
            ):
                phrase.add_pre_modifier(modifier_word)
                return
        #  default case
        phrase.add_post_modifier(modifier_element)

    def realise(self, phrase):
        realised = ListElement()
        # Creates the appropriate pronoun if the noun phrase
        # is pronominal.
        if phrase.pronominal:
            pronoun = self.create_pronoun()
            realised.append(pronoun)
        else:
            du = phrase.lexicon.first('du', category=DETERMINER)
            un = phrase.lexicon.first('un', category=DETERMINER)
            de = phrase.lexicon.first('de', category=COMPLEMENTISER)
            if not phrase.raised and phrase.specifier == du:
                de = phrase.lexicon.first('du', category=DETERMINER)
                realised_de = de.realise_syntax()
                realised_de.features[DISCOURSE_FUNCTION] = SPECIFIER
                realised.append(realised_de)
                sub_phrase = NounPhraseElement(phrase)
                # if the noun phrase is the direct object of a negated verb,
                # the determiner is reduced to "de" instead of "du"
                if self.is_negated_phrase(phrase):
                    new_determiner = None
                else:
                    new_determiner = phrase.lexicon.get('le', category=DETERMINER)
                sub_phrase.specifier = new_determiner
                realised_subphrase = super(FrenchNounPhraseHelper, self).realise()
                realised.append(realised_subphrase)
            elif (
                    not phrase.raised and
                    phrase.specifier == un and
                    self.is_negated_phrase(phrase)
            ):
                phrase.specifier = de
                realised = super(FrenchNounPhraseHelper, self).realise(phrase)
            else:
                realised = super(FrenchNounPhraseHelper, self).realise(phrase)
        return realised
