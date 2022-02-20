
from .base import NounPhraseHelper, PhraseHelper
from nlglib.spec.base import NLGElement
from nlglib.spec.list import ListElement
from nlglib.spec.string import StringElement
from nlglib.spec.phrase import AdjectivePhraseElement, PhraseElement, CoordinatedPhraseElement
from nlglib.spec.word import WordElement, InflectedWordElement
from nlglib.lexicon import feature
from nlglib.lexicon.feature import category, number, person, gender, tense

__all__ = ['EnglishPhraseHelper', 'EnglishNounPhraseHelper']


class EnglishPhraseHelper(PhraseHelper):
    """A syntax defining specific behaviour for English sentences."""


# noinspection PyMethodMayBeStatic
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
            new_pronoun_infl_elt.discourse_function = feature.discourse.SPECIFIER
        new_pronoun_infl_elt.possessive = phrase.possessive
        return new_pronoun_infl_elt


# noinspection PyMethodMayBeStatic
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
                          discourse_function=feature.discourse.PRE_MODIFIER)
        self.realise_coordinates(phrase=phrase, realised_element=realised)
        self.realise_list(realised_element=realised,
                          element_list=phrase.postmodifiers,
                          discourse_function=feature.discourse.POST_MODIFIER)
        self.realise_complements(phrase=phrase, realised_element=realised)
        return realised

    def realise_coordinates(self, phrase, realised_element):
        """Realises the complements of the phrase."""
        coordinates = phrase.features[feature.internal.COORDINATES] or []
        if not coordinates:
            return

        realisation = ListElement()

        conjunction = phrase.lexicon.first(phrase.conjunction, category=category.CONJUNCTION).inflex(
            discourse_function=feature.discourse.CONJUNCTION
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


# noinspection PyMethodMayBeStatic
class VerbPhraseHelper(PhraseHelper):
    """This class contains static methods to help the syntax processor realise verb
    phrases. It adds auxiliary verbs into the element tree as required.
    """

    def realise(self, phrase):
        if not phrase or phrase.elided:
            return None

        realised_element = ListElement()
        main_verb_realisation = []
        auxiliary_realisation = []

        vg_components = self._create_verb_group(phrase)
        self._split_verb_group(vg_components, main_verb_realisation, auxiliary_realisation)

        if phrase.realise_auxiliary:
            self._realise_auxiliaries(realised_element, auxiliary_realisation)
            self.realise_list(realised_element, phrase.premodifiers, feature.discourse.PRE_MODIFIER)
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)
        elif self._is_copular(phrase.head):
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)
            self.realise_list(realised_element, phrase.premodifiers, feature.discourse.PRE_MODIFIER)
        else:
            self.realise_list(realised_element, phrase.premodifiers, feature.discourse.PRE_MODIFIER)
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)

        self.realise_complements(phrase, realised_element)
        self.realise_list(realised_element, phrase.postmodifiers, feature.discourse.POST_MODIFIER)

        return realised_element

    def _create_verb_group(self, phrase):
        """Creates a stack of verbs for the verb phrase.

        Additional auxiliary verbs are added as required based on the features of the verb phrase.
        """
        form_value = phrase.form
        tense_value = phrase.tense
        modal = phrase.modal
        modal_past = False
        actual_modal = None
        vg_components = []
        interrogative = phrase.interrogative_type

        if form_value == feature.form.GERUND or form_value == feature.form.INFINITIVE:
            tense_value = tense.PRESENT

        if form_value == feature.form.INFINITIVE:
            actual_modal = "to"
        elif form_value is None or form_value == feature.form.NORMAL:
            if (
                tense_value == tense.FUTURE
                and modal is None
                and (
                    not isinstance(phrase.head, CoordinatedPhraseElement)
                    or (isinstance(phrase.head, CoordinatedPhraseElement) and interrogative)
                )
            ):
                actual_modal = "will"
            elif modal is not None:
                actual_modal = modal

                if tense_value == tense.PAST:
                    modal_past = True

        self._push_particles(phrase, vg_components)
        front_vg = self._grab_head_verb(phrase, tense_value, has_modal=modal is not None)
        self._check_imperative_infinitive(form_value, front_vg)

        if phrase.passive:
            front_vg = self._add_be(front_vg, vg_components, feature.form.PAST_PARTICIPLE)

        if phrase.progressive:
            front_vg = self._add_be(front_vg, vg_components, feature.form.PRESENT_PARTICIPLE)

        if phrase.perfect or modal_past:
            front_vg = self._add_have(front_vg, vg_components, modal, tense_value)

        front_vg = self._push_if_modal(actual_modal is not None, phrase, front_vg, vg_components)
        front_vg = self._create_not(phrase, vg_components, front_vg, modal is not None)

        if front_vg is not None:
            self._push_front_verb(phrase, vg_components, front_vg, form_value, interrogative)

        self._push_modal(actual_modal, phrase, vg_components)
        return vg_components

    def _push_particles(self, phrase, vg_components):
        particle = phrase.particle
        if particle and isinstance(particle, str):
            vg_components.append(StringElement(particle))
        elif isinstance(particle, NLGElement):
            vg_components.append(particle.realise())

    def _grab_head_verb(self, phrase, tense_value, has_modal):
        """Grabs the head verb of the verb phrase and sets it to future tense if the
        phrase is future tense. It also turns off negation if the group has a modal.
        """
        front_vg = phrase.head
        if not front_vg:
            return
        if isinstance(front_vg, WordElement):
            front_vg = InflectedWordElement(front_vg)

        if not front_vg.tense:
            front_vg.tense = tense_value

        if has_modal:
            front_vg.negated = False

        return front_vg

    def _check_imperative_infinitive(self, form_value, front_vg):
        """Checks to see if the phrase is in imperative, infinitive or bare
        infinitive form. If it is then no morphology is done on the main verb.
        """
        if (
            form_value == feature.form.IMPERATIVE
            or form_value == feature.form.INFINITIVE
            or form_value == feature.form.BARE_INFINITIVE
        ) and front_vg is not None:
            front_vg.non_morph = True

    def _add_be(self, front_vg, vg_components, front_form):
        if front_vg:
            front_form.form = front_form
            vg_components.append(front_vg)
        # TODO: "be" has to be WordElement -- set lexicon on class and do lookup?
        return InflectedWordElement("be", category.VERB)

    def _add_have(self, front_vg, vg_components, modal, tense_value):
        """Adds <em>have</em> to the stack."""
        if front_vg:
            front_vg.form = feature.form.PAST_PARTICIPLE
            vg_components.append(front_vg)

        new_front = InflectedWordElement("have", category.VERB)
        new_front.tense = tense_value
        if modal:
            new_front.non_morph = True
        return new_front

    def _push_if_modal(self, has_modal, phrase, front_vg, vg_components):
        """Pushes the front verb on to the stack if the phrase has a modal."""
        new_front = front_vg
        if has_modal and not phrase.ignore_modal:
            if front_vg:
                front_vg.non_morph = True
                vg_components.append(front_vg)
            new_front = None
        return new_front

    def _create_not(self, phrase, vg_components, front_vg, has_modal):
        """Adds <em>not</em> to the stack if the phrase is negated."""
        new_front = front_vg
        if not phrase.negated:
            return new_front

        # before adding "do", check if this is an object WH interrogative
        # in which case, don't add anything as it's already done by ClauseHelper
        interr_type = phrase.interrogative_type
        add_do = interr_type not in (feature.interrogative_type.WHAT_OBJECT, feature.interrogative_type.WHO_OBJECT)

        if vg_components or front_vg and self._is_copular(front_vg):
            vg_components.append(InflectedWordElement("not", category.ADVERB))
        else:
            if front_vg and not has_modal:
                front_vg.negated = True
                vg_components.append(front_vg)

            vg_components.append(InflectedWordElement("not", category.ADVERB))

            if add_do:
                new_front = InflectedWordElement("do", category.VERB)
        return new_front

    def _is_copular(self, element):
        """Check to see if the base of the word is copular, i.e., 'be'"""
        if isinstance(element, (InflectedWordElement, WordElement)):
            return element.base_form == 'be'
        if isinstance(element, PhraseElement):
            # get the head and check if it's "be"
            # if isinstance(element, Clause):
            #     head = element.verb
            # else:
            head = element.head
            if head:
                return isinstance(head, (InflectedWordElement, WordElement)) and head.base_form == 'be'
        return False

    def _push_front_verb(self, phrase, vg_components, front_vg, form_value, interrogative):
        """Add the front verb into the verb components"""
        interrogative_type = phrase.interrogative_type
    
        if form_value == feature.form.GERUND:
            front_vg.form = feature.form.PRESENT_PARTICIPLE
            vg_components.append(front_vg)
        elif form_value == feature.form.PAST_PARTICIPLE:
            front_vg.form = feature.form.PAST_PARTICIPLE
            vg_components.append(front_vg)
        elif form_value == feature.form.PRESENT_PARTICIPLE:
            front_vg.form = feature.form.PRESENT_PARTICIPLE
        elif (
            (feature.form.NORMAL != form_value or interrogative)
            and not self._is_copular(phrase.getHead())
            and not vg_components
        ):
            if interrogative_type in (
                feature.interrogative_type.WHO_SUBJECT,
                feature.interrogative_type.WHAT_SUBJECT,
            ):
                front_vg.non_morph = True
            vg_components.append(front_vg)
        else:
            front_vg.tense = phrase.tense
            front_vg.person = phrase.person
            front_vg.number = self._determine_number(phrase.parent, phrase)
    
            # don't push the front VG if it's a negated interrogative WH object question
            if not (
                phrase.negated
                and interrogative_type
                in (
                    feature.interrogative_type.WHO_OBJECT,
                    feature.interrogative_type.WHAT_OBJECT,
                )
            ):
                vg_components.append(front_vg)

    def _determine_number(self, parent, phrase):
        """Determines the number agreement for the phrase ensuring that any number
        agreement on the parent element is inherited by the phrase.
        """
        number_value = phrase.number or number.SINGULAR

        if isinstance(parent, PhraseElement):
            if parent.category == category.CLAUSE and (
                PhraseHelper().is_expletive_subject(parent)
                or parent.interrogative_type
                in (
                    feature.interrogative_type.WHO_SUBJECT,
                    feature.interrogative_type.WHAT_SUBJECT,
                )
                and self._is_copular(phrase.head)
            ):
                if self._has_plural_complement(phrase.complements):
                    number_value = number.PLURAL
                else:
                    number_value = number.SINGULAR

        return number_value

    def _has_plural_complement(self, complements):
        """Checks to see if any of the complements to the phrase are plural."""
        return any((c.category == category.NOUN_PHRASE and c.number == number.PLURAL) for c in complements)

    def _push_modal(self, actual_modal, phrase, vg_components):
        """Pushes the modal onto the stack of verb components."""
        if actual_modal and not phrase.ignore_modal:
            vg_components.append(InflectedWordElement(actual_modal, category.MODAL))

    def _split_verb_group(self, vg_components, main_verb_realisation, auxiliary_realisation):
        """Splits the stack of verb components into two sections. One being the verb
        associated with the main verb group, the other being associated with the
        auxiliary verb group.
        """
        main_verb_seen = False

        for word in vg_components:
            if not main_verb_seen:
                main_verb_realisation.append(word)
                if word != 'not':
                    main_verb_seen = True
            else:
                auxiliary_realisation.append(word)

    def _realise_auxiliaries(self, realised_element, auxiliary_realisation):
        """Realises the auxiliary verbs in the verb group."""
        while auxiliary_realisation:
            aux = auxiliary_realisation.pop()
            current_element = aux.realise()
            if current_element:
                realised_element.append(current_element)
                current_element.discourse_function = feature.discourse.AUXILIARY

    def _realise_main_verb(self, phrase, main_verb_realisation, realised_element):
        """Realises the main group of verbs in the phrase."""
        while main_verb_realisation:
            main = main_verb_realisation.pop()
            main.interrogative_type = phrase.interrogative_type
            current_element = main.realise_syntax()
            if current_element:
                realised_element.append(current_element)


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
