import typing as t

from .base import NounPhraseHelper, PhraseHelper
from nlglib.spec.base import NLGElement
from nlglib.spec.list import ListElement
from nlglib.spec.string import StringElement
from nlglib.spec.phrase import (
    AdjectivePhraseElement,
    PhraseElement,
    CoordinatedPhraseElement,
    PrepositionPhraseElement,
)
from nlglib.spec.phrase import VerbPhraseElement, Clause
from nlglib.spec.word import WordElement, InflectedWordElement
from nlglib.lexicon import feature as f
from nlglib.lexicon.feature import category, number, person, gender, tense
from nlglib.lexicon.feature import interrogative_type, discourse

__all__ = ["EnglishPhraseHelper", "EnglishNounPhraseHelper"]


class EnglishPhraseHelper(PhraseHelper):
    """A syntax defining specific behaviour for English sentences."""


# noinspection PyMethodMayBeStatic
class EnglishNounPhraseHelper(NounPhraseHelper):
    """A syntax defining specific behaviour for English noun phrases."""

    def add_modifier(self, phrase, modifier):
        """Add the argument modifier to the phrase pre/post modifier list."""
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
            elif " " not in modifier:
                modifier_element = WordElement(
                    base_form=modifier,
                    realisation=modifier,
                    lexicon=phrase.lexicon,
                    category=category.ADJECTIVE,
                )
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
                word = "I"
            elif phrase.person == person.SECOND:
                word = "you"
            else:
                if phrase.gender == gender.FEMININE:
                    word = "she"
                elif phrase.gender == gender.MASCULINE:
                    word = "he"
                else:
                    word = "it"
        elif phrase.number == number.PLURAL:
            if phrase.person == person.FIRST:
                word = "we"
            elif phrase.person == person.SECOND:
                word = "you"
            else:
                word = "they"
        else:
            word = "both"

        new_pronoun_elt = phrase.lexicon.first(word, category=category.PRONOUN)
        new_pronoun_infl_elt = new_pronoun_elt.inflex(
            discourse_function=phrase.discourse_function
        )
        new_pronoun_infl_elt.gender = phrase.gender
        new_pronoun_infl_elt.person = phrase.person
        new_pronoun_infl_elt.number = phrase.number
        if phrase.discourse_function:
            new_pronoun_infl_elt.discourse_function = phrase.discourse_function
        else:
            new_pronoun_infl_elt.discourse_function = discourse.SPECIFIER
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
        self.realise_list(
            realised_element=realised,
            element_list=phrase.premodifiers,
            discourse_function=discourse.PRE_MODIFIER,
        )
        self.realise_coordinates(phrase=phrase, realised_element=realised)
        self.realise_list(
            realised_element=realised,
            element_list=phrase.postmodifiers,
            discourse_function=discourse.POST_MODIFIER,
        )
        self.realise_complements(phrase=phrase, realised_element=realised)
        return realised

    def realise_coordinates(self, phrase, realised_element):
        """Realises the complements of the phrase."""
        coordinates = phrase.coordinates or []
        if not coordinates:
            return

        realisation = ListElement()

        conjunction = (
            phrase.lexicon.first(
                phrase.conjunction, category=category.CONJUNCTION
            ).inflex(discourse_function=discourse.CONJUNCTION)
            if phrase.conjunction
            else None
        )

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
        self._split_verb_group(
            vg_components, main_verb_realisation, auxiliary_realisation
        )

        if phrase.realise_auxiliary:
            self._realise_auxiliaries(realised_element, auxiliary_realisation)
            self.realise_list(
                realised_element, phrase.premodifiers, discourse.PRE_MODIFIER
            )
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)
        elif self.is_copular(phrase.head):
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)
            self.realise_list(
                realised_element, phrase.premodifiers, discourse.PRE_MODIFIER
            )
        else:
            self.realise_list(
                realised_element, phrase.premodifiers, discourse.PRE_MODIFIER
            )
            self._realise_main_verb(phrase, main_verb_realisation, realised_element)

        self.realise_complements(phrase, realised_element)
        self.realise_list(
            realised_element, phrase.postmodifiers, discourse.POST_MODIFIER
        )

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

        if form_value == f.form.GERUND or form_value == f.form.INFINITIVE:
            tense_value = tense.PRESENT

        if form_value == f.form.INFINITIVE:
            actual_modal = "to"
        elif form_value is None or form_value == f.form.NORMAL:
            if (
                tense_value == tense.FUTURE
                and modal is None
                and (
                    not isinstance(phrase.head, CoordinatedPhraseElement)
                    or (
                        isinstance(phrase.head, CoordinatedPhraseElement)
                        and interrogative
                    )
                )
            ):
                actual_modal = "will"
            elif modal is not None:
                actual_modal = modal

                if tense_value == tense.PAST:
                    modal_past = True

        self._push_particles(phrase, vg_components)
        front_vg = self._grab_head_verb(
            phrase, tense_value, has_modal=modal is not None
        )
        self._check_imperative_infinitive(form_value, front_vg)

        if phrase.passive:
            front_vg = self._add_be(front_vg, vg_components, f.form.PAST_PARTICIPLE)

        if phrase.progressive:
            front_vg = self._add_be(front_vg, vg_components, f.form.PRESENT_PARTICIPLE)

        if phrase.perfect or modal_past:
            front_vg = self._add_have(front_vg, vg_components, modal, tense_value)

        front_vg = self._push_if_modal(
            actual_modal is not None, phrase, front_vg, vg_components
        )
        front_vg = self._create_not(phrase, vg_components, front_vg, modal is not None)

        if front_vg is not None:
            self._push_front_verb(
                phrase, vg_components, front_vg, form_value, interrogative
            )

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
            form_value == f.form.IMPERATIVE
            or form_value == f.form.INFINITIVE
            or form_value == f.form.BARE_INFINITIVE
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
            front_vg.form = f.form.PAST_PARTICIPLE
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
        add_do = interr_type not in (
            interrogative_type.WHAT_OBJECT,
            interrogative_type.WHO_OBJECT,
        )

        if vg_components or front_vg and self.is_copular(front_vg):
            vg_components.append(InflectedWordElement("not", category.ADVERB))
        else:
            if front_vg and not has_modal:
                front_vg.negated = True
                vg_components.append(front_vg)

            vg_components.append(InflectedWordElement("not", category.ADVERB))

            if add_do:
                new_front = InflectedWordElement("do", category.VERB)
        return new_front

    @staticmethod
    def is_copular(element):
        """Check to see if the base of the word is copular, i.e., 'be'"""
        if isinstance(element, (InflectedWordElement, WordElement)):
            return element.base_form == "be"
        if isinstance(element, PhraseElement):
            # get the head and check if it's "be"
            if isinstance(element, Clause):
                head = element.verb
            else:
                head = element.head
            if head:
                return (
                    isinstance(head, (InflectedWordElement, WordElement))
                    and head.base_form == "be"
                )
        return False

    def _push_front_verb(
        self, phrase, vg_components, front_vg, form_value, interrogative
    ):
        """Add the front verb into the verb components"""
        if form_value == f.form.GERUND:
            front_vg.form = f.form.PRESENT_PARTICIPLE
            vg_components.append(front_vg)
        elif form_value == f.form.PAST_PARTICIPLE:
            front_vg.form = f.form.PAST_PARTICIPLE
            vg_components.append(front_vg)
        elif form_value == f.form.PRESENT_PARTICIPLE:
            front_vg.form = f.form.PRESENT_PARTICIPLE
        elif (
            (f.form.NORMAL != form_value or interrogative)
            and not self.is_copular(phrase.getHead())
            and not vg_components
        ):
            if phrase.interrogative_type in (
                interrogative_type.WHO_SUBJECT,
                interrogative_type.WHAT_SUBJECT,
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
                and phrase.interrogative_type
                in (
                    interrogative_type.WHO_OBJECT,
                    interrogative_type.WHAT_OBJECT,
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
                    interrogative_type.WHO_SUBJECT,
                    interrogative_type.WHAT_SUBJECT,
                )
                and self.is_copular(phrase.head)
            ):
                if self._has_plural_complement(phrase.complements):
                    number_value = number.PLURAL
                else:
                    number_value = number.SINGULAR

        return number_value

    def _has_plural_complement(self, complements):
        """Checks to see if any of the complements to the phrase are plural."""
        return any(
            (c.category == category.NOUN_PHRASE and c.number == number.PLURAL)
            for c in complements
        )

    def _push_modal(self, actual_modal, phrase, vg_components):
        """Pushes the modal onto the stack of verb components."""
        if actual_modal and not phrase.ignore_modal:
            vg_components.append(InflectedWordElement(actual_modal, category.MODAL))

    def _split_verb_group(
        self, vg_components, main_verb_realisation, auxiliary_realisation
    ):
        """Splits the stack of verb components into two sections. One being the verb
        associated with the main verb group, the other being associated with the
        auxiliary verb group.
        """
        main_verb_seen = False

        for word in vg_components:
            if not main_verb_seen:
                main_verb_realisation.append(word)
                if word != "not":
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
                current_element.discourse_function = discourse.AUXILIARY

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


class ClauseHelper(EnglishPhraseHelper):
    def realise(self, phrase):

        if not phrase:
            return None

        split_verb: t.Optional[NLGElement] = None
        interrog_obj: bool = False
        realised_element = ListElement()
        verb_element = phrase.verb_phrase

        if not verb_element:
            verb_element = phrase.head

        self.check_subject_number_person(phrase, verb_element)
        self.check_discourse_function(phrase)
        self.copy_front_modifiers(phrase, verb_element)
        self.add_complementiser(phrase, realised_element)
        self.add_cue_phrase(phrase, realised_element)

        if phrase.interrogative_type:
            inter = phrase.interrogative_type
            it = interrogative_type
            interrog_obj = inter in (
                it.WHAT_OBJECT,
                it.WHO_OBJECT,
                it.HOW_PREDICATE,
                it.HOW,
                it.WHY,
                it.WHERE,
            )
            split_verb = self.realise_interrogative(
                phrase, realised_element, verb_element
            )
        else:
            self.realise_list(
                realised_element, phrase.front_modifiers, discourse.FRONT_MODIFIER
            )

        self.add_subjects_to_front(phrase, realised_element, split_verb)

        passive_split_verb: NLGElement = self.add_passive_complements_number_person(
            phrase, realised_element, verb_element
        )

        if passive_split_verb:
            split_verb = passive_split_verb

        # realise verb needs to know if clause is object interrogative
        self.realise_verb(
            phrase, realised_element, split_verb, verb_element, interrog_obj
        )
        self.add_passive_subjects(phrase, realised_element)
        self.add_interrogative_front_modifiers(phrase, realised_element)
        self.add_ending_to(phrase, realised_element)

        return realised_element

    def add_ending_to(self, phrase, realised_element):
        """
        Add <em>to</em> to the end of interrogatives concerning indirect
        objects. For example, <em>who did John give the flower <b>to</b></em>.
        """
        if phrase.interrogative_type == interrogative_type.WHO_INDIRECT_OBJECT:
            word = phrase.lexicon.first("to", category.PREPOSITION)
            realised_element.append(word.realise())

    def add_interrogative_front_modifiers(self, phrase, realised_element):
        """Add the front modifiers to the end of the clause when dealing with interrogatives."""
        if phrase.interrogative_type:
            for subject in phrase.fron_modifiers:
                current_element = subject.realise()
                if current_element:
                    current_element.discourse_function = discourse.FRONT_MODIFIER
                    realised_element.append(current_element)

    def add_passive_subjects(self, phrase, realised_element):
        """Realise the subjects of a passive clause"""
        if not phrase.passive:
            return

        all_subjects = phrase.subjects
        if all_subjects or phrase.interrogative_type:
            pp = PrepositionPhraseElement(lexicon=phrase.lexicon)
            pp.preposition = "by"
            realised_element.append(pp.realise())

        for subject in all_subjects:
            subject.passive = True
            if subject.category == category.NOUN_PHRASE or isinstance(
                subject, CoordinatedPhraseElement
            ):
                current_element = subject.realise()
                current_element.discourse_function = discourse.SUBJECT
                realised_element.append(current_element)

    def realise_verb(
        self, phrase, realised_element, split_verb, verb_element, interrog_obj
    ):
        """Realise the verb part of the clause"""
        self.set_verb_features(phrase, verb_element)

        current_element = verb_element.realise()
        if not current_element:
            return

        if not split_verb:
            current_element.discourse_function = discourse.VERB_PHRASE
            realised_element.append(current_element)
        else:
            if isinstance(current_element, ListElement):
                children = current_element.children
                current_element = children[0]
                current_element.discourse_function = discourse.VERB_PHRASE
                realised_element.append(current_element)
                realised_element.append(split_verb)

                for current_element in children[1:]:
                    current_element.discourse_function = discourse.VERB_PHRASE
                    realised_element.append(current_element)
            else:
                current_element.discourse_function = discourse.VERB_PHRASE

                if interrog_obj:
                    realised_element.append(current_element)
                    realised_element.append(split_verb)
                else:
                    realised_element.append(split_verb)
                    realised_element.append(current_element)

    def set_verb_features(self, phrase, verb_element):
        pass
        # // this routine copies features from the clause to the VP.
        # // it is disabled, as this copying is now done automatically
        # // when features are set in SPhraseSpec
        # // if (verbElement != null) {
        # // verbElement.setFeature(f.INTERROGATIVE_TYPE, phrase
        # // .getFeature(f.INTERROGATIVE_TYPE));
        # // verbElement.setFeature(InternalFeature.COMPLEMENTS, phrase
        # // .getFeature(InternalFeature.COMPLEMENTS));
        # // verbElement.setFeature(InternalFeature.PREMODIFIERS, phrase
        # // .getFeature(InternalFeature.PREMODIFIERS));
        # // verbElement.setFeature(f.FORM, phrase
        # // .getFeature(f.FORM));
        # // verbElement.setFeature(f.MODAL, phrase
        # // .getFeature(f.MODAL));
        # // verbElement.setNegated(phrase.isNegated());
        # // verbElement.setFeature(f.PASSIVE, phrase
        # // .getFeature(f.PASSIVE));
        # // verbElement.setFeature(f.PERFECT, phrase
        # // .getFeature(f.PERFECT));
        # // verbElement.setFeature(f.PROGRESSIVE, phrase
        # // .getFeature(f.PROGRESSIVE));
        # // verbElement.setTense(phrase.getTense());
        # // verbElement.setFeature(f.FORM, phrase
        # // .getFeature(f.FORM));
        # // verbElement.setFeature(LexicalFeature.GENDER, phrase
        # // .getFeature(LexicalFeature.GENDER));
        # // }

    def add_passive_complements_number_person(
        self, phrase, realised_element, verb_element
    ):
        """Realises the complements of passive clauses; also sets number, person for passive"""

        passive_number = None
        passive_person = None
        split_verb = None
        verb_phrase = phrase.verb_phrase

        num_comps = 0
        coord_subj = False

        if (
            phrase.passive
            and verb_phrase
            and phrase.interrogative_type != interrogative_type.WHAT_OBJECT
        ):
            # complements of a clause are stored in the VPPhraseSpec
            for subject in verb_phrase.complements:
                if subject.discourse_function == discourse.OBJECT:
                    subject.passive = True
                    num_comps += 1
                    current_element = subject.realise()

                    if current_element:
                        current_element.discourse_function = discourse.OBJECT

                        if phrase.interrogative_type:
                            split_verb = current_element
                        else:
                            realised_element.append(current_element)

                    if not coord_subj and isinstance(subject, CoordinatedPhraseElement):
                        conj = subject.conjunction
                        coord_subj = conj == "and"

                    if not passive_number:
                        passive_number = subject.number or number.PLURAL

                    if subject.person == person.FIRST:
                        passive_person = person.FIRST
                    elif (
                        subject.person == person.SECOND
                        and passive_person != person.FIRST
                    ):
                        passive_person = person.SECOND
                    elif not passive_person:
                        passive_person = person.THIRD

                    if (
                        phrase.form == f.form.GERUND
                        and not phrase.suppress_genitive_in_gerund
                    ):
                        subject.possessive = True

        if verb_element:
            if passive_person:
                verb_element.person = passive_person

            if num_comps > 1 or coord_subj:
                verb_element.number = number.PLURAL
            elif passive_number:
                verb_element.number = passive_number

        return split_verb

    def add_subjects_to_front(self, phrase, realised_element, split_verb):
        """Adds the subjects to the beginning of the clause unless the clause is
        infinitive, imperative or passive, or the subjects split the verb."""

        if (
            phrase.form != f.form.INFINITIVE
            and phrase.form != f.form.IMPERATIVE
            and not phrase.passive
            and not split_verb
        ):
            realised_element.extend(self.realise_subjects(phrase).children)

    def realise_subjects(self, phrase):
        """Realise the subjects of the clause"""
        realised_element = ListElement()
        for subject in phrase.subjects:
            subject.discourse_function = discourse.SUBJECT
            if phrase.form == f.form.GERUND and not phrase.suppress_genitive_in_gerund:
                subject.possessive = True
            current_element = subject.realise()
            if current_element:
                realised_element.append(current_element)

        return realised_element

    def realise_interrogative(self, phrase, realised_element, verb_element):
        """This is the main controlling method for handling interrogative clauses.

        The actual steps taken are dependent on the type of question being asked.
        The method also determines if there is a subject that will split the verb
        group of the clause. For example, the clause
        <em>the man <b>should give</b> the woman the flower</em> has the verb
        group indicated in <b>bold</b>. The phrase is rearranged as yes/no
        question as
        <em><b>should</b> the man <b>give</b> the woman the flower</em> with the
        subject <em>the man</em> splitting the verb group.
        """

        split_verb = None

        if phrase.parent:
            phrase.patent.interrogative = True

        itype = phrase.interrogative_type
        if not itype:
            return

        if itype == interrogative_type.YES_NO:
            split_verb = self.realise_yes_no(phrase, verb_element, realised_element)
        elif itype in (interrogative_type.WHO_SUBJECT, interrogative_type.WHAT_SUBJECT):
            self.realise_interrogative_key_word(
                itype, category.PRONOUN, realised_element
            )
            del phrase['subjects']
        elif itype == interrogative_type.HOW_MANY:
            self.realise_interrogative_key_word(
                "how", category.PRONOUN, realised_element
            )
            self.realise_interrogative_key_word(
                "many", category.ADVERB, realised_element
            )
        elif itype == interrogative_type.HOW_PREDICATE:
            split_verb = self.realise_object_wh_interrogative(
                "how", phrase, realised_element
            )
        elif itype in (
            interrogative_type.HOW,
            interrogative_type.WHY,
            interrogative_type.WHERE,
            interrogative_type.WHO_OBJECT,
            interrogative_type.WHO_INDIRECT_OBJECT,
            interrogative_type.WHAT_OBJECT,
        ):
            split_verb = self.realise_object_wh_interrogative(
                itype, phrase, realised_element
            )

        return split_verb

    def realise_object_wh_interrogative(self, itype, phrase, realised_element):
        """Controls the realisation of <em>wh</em> object questions"""
        split_verb = None
        self.realise_interrogative_key_word(itype, category.PRONOUN, realised_element)
        if not self.has_auxiliary(phrase) and not VerbPhraseHelper.is_copular(phrase):
            self.add_do_auxiliary(phrase, realised_element)
        elif not phrase.passive:
            split_verb = self.realise_subjects(phrase)

        return split_verb

    def has_auxiliary(self, phrase):
        return (
            phrase.modal
            or phrase.perfecr
            or phrase.progressive
            or phrase.tense == tense.FUTURE
        )

    def add_do_auxiliary(self, phrase, realised_element):
        """Adds a <em>do</em> verb to the realisation of this clause."""
        do_phrase = VerbPhraseElement(phrase.lexicon)
        do_phrase.verb = "do"
        do_phrase.tense = phrase.tense
        do_phrase.person = phrase.person
        do_phrase.number = phrase.number
        realised_element.append(do_phrase.realise())

    def realise_interrogative_key_word(self, itype, word_category, realised_element):
        """Realises the key word of the interrogative. For example, <em>who</em>, <em>what</em>"""
        if not itype:
            return
        question = WordElement(itype, word_category)
        current_element = question.realise_syntax()
        if current_element:
            realised_element.append(current_element)

    def realise_yes_no(self, phrase, verb_element, realised_element):
        """Performs the realisation for YES/NO types of questions

        This may involve
        adding an optional <em>do</em> auxiliary verb to the beginning of the
        clause. The method also determines if there is a subject that will split
        the verb group of the clause. For example, the clause
        <em>the man <b>should give</b> the woman the flower</em> has the verb
        group indicated in <b>bold</b>. The phrase is rearranged as yes/no
        question as
        <em><b>should</b> the man <b>give</b> the woman the flower</em> with the
        subject <em>the man</em> splitting the verb group.
        """
        split_verb = None

        if (
            not (
                isinstance(verb_element, VerbPhraseElement)
                and VerbPhraseHelper.is_copular(verb_element.verb)
            )
            and not phrase.progressive
            and not phrase.modal
            and not phrase.tense == tense.FUTURE
            and not phrase.negated
            and not phrase.passive
        ):
            self.add_do_auxiliary(phrase, realised_element)
        else:
            split_verb = self.realise_subjects(phrase)
        return split_verb

    def add_cue_phrase(self, phrase, realised_element):
        """Realises the cue phrase for the clause if it exists."""
        current_element = phrase.cue_phrase.realise() if phrase.cue_phrase else None
        if current_element:
            current_element.discourse_function = discourse.CUE_PHRASE
            realised_element.append(current_element)

    def add_complementiser(self, phrase, realised_element):
        """Checks to see if this clause is a subordinate clause. If it is then the
        complementiser is added as a component to the realised element
        <b>unless</b> the complementiser has been suppressed.
        """
        if (
            phrase.clause_status == f.clause.SUBORDINATE
            and not phrase.suppressed_complementiser
        ):
            current_element = (
                phrase.complementiser.realise() if phrase.complementiser else None
            )
            if current_element:
                realised_element.append(current_element)

    def copy_front_modifiers(self, phrase, verb_element):
        """Copies the front modifiers of the clause to the list of post-modifiers of
        the verb only if the phrase has infinitive form.
        """
        front_modifiers = phrase.front_modifiers or []
        clause_form = phrase.form

        if verb_element is None:
            return

        phrase_post_modifiers = phrase.postmodifiers or []
        if isinstance(verb_element, PhraseElement):
            verb_post_modifiers = verb_element.postmodifiers or []
            for modifier in phrase_post_modifiers:
                if modifier not in verb_post_modifiers:
                    verb_element.add_post_modifier(modifier)

        if clause_form == f.form.INFINITIVE:
            phrase.suppressed_complementiser = True
            for modifier in front_modifiers:
                if isinstance(verb_element, PhraseElement):
                    verb_element.add_post_modifier(modifier)
            del phrase['front_modifiers']
            verb_element.non_morph = True

    def check_discourse_function(self, phrase):
        """Checks the discourse function of the clause and alters the form of the clause as necessary

        The following algorithm is used: <br>
        *
        * <pre>
        * If the clause represents a direct or indirect object then
        *      If form is currently Imperative then
        *           Set form to Infinitive
        *           Suppress the complementiser
        *      If form is currently Gerund and there are no subjects
        *      	 Suppress the complementiser
        * If the clause represents a subject then
        *      Set the form to be Gerund
        *      Suppress the complementiser
        * </pre>
        """
        subjects = phrase.subjects or []
        clause_form = phrase.form
        discourse_value = phrase.discourse_function

        if discourse_value in (discourse.OBJECT, discourse.INDIRECT_OBJECT):
            if clause_form == f.form.IMPERATIVE:
                phrase.suppressed_complementiser = True
                phrase.form = f.form.INFINITIVE
            elif clause_form == f.form.GERUND and not subjects:
                phrase.suppressed_complementiser = True
        elif discourse_value == discourse.SUBJECT:
            phrase.form = f.form.GERUND
            phrase.suppressed_complementiser = True

    def check_subject_number_person(self, phrase, verb_element):
        """Checks the subjects of the phrase to determine if there is more than one
        subject. This ensures that the verb phrase is correctly set. Also set
        person correctly
        """
        subjects = phrase.subjects or []
        plural_subjects = False
        inferred_person = None

        if len(subjects) == 1:
            current_element = subjects[0]
            # coordinated NP with "and" are plural (not coordinated NP with "or")
            if (
                isinstance(current_element, CoordinatedPhraseElement)
                and current_element.check_if_plural()
            ):
                plural_subjects = True
            elif current_element.number == number.PLURAL and not isinstance(
                current_element, Clause
            ):
                plural_subjects = True
            elif current_element.category == category.NOUN_PHRASE:
                head = current_element.head
                inferred_person = current_element.person
                if not head:
                    plural_subjects = False
                elif head.number == number.PLURAL:
                    plural_subjects = True
                elif isinstance(head, ListElement):
                    plural_subjects = True
        if verb_element:
            verb_element.number = number.PLURAL if plural_subjects else phrase.number
            if inferred_person:
                verb_element.person = inferred_person
