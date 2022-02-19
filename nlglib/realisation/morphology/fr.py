# encoding: utf-8

"""Definition of French morphology rules."""


import re

from collections import namedtuple

from nlglib.lexicon.feature.gender import FEMININE, MASCULINE, NEUTER
from nlglib.lexicon.feature.discourse import (
    HEAD, FRONT_MODIFIER, PRE_MODIFIER, POST_MODIFIER,
    OBJECT, COMPLEMENT, SUBJECT, INDIRECT_OBJECT)
from nlglib.lexicon.feature.category import (
    VERB_PHRASE, NOUN, VERB, PREPOSITIONAL_PHRASE, NOUN_PHRASE, PRONOUN, CLAUSE)
from nlglib.lexicon.feature.lexical import REFLEXIVE, GENDER, PRONOUN_TYPE
from nlglib.lexicon.feature.pronoun import PERSONAL, RELATIVE
from nlglib.lexicon.feature.lexical.fr import DETACHED
from nlglib.lexicon.feature.person import FIRST, SECOND, THIRD
from nlglib.lexicon.feature.form import IMPERATIVE
from nlglib.lexicon.feature.number import SINGULAR, PLURAL, BOTH
from nlglib.lexicon.feature.tense import PRESENT, FUTURE, CONDITIONAL, PAST
from nlglib.lexicon.feature import PERSON, NUMBER
from nlglib.lexicon.feature.internal import DISCOURSE_FUNCTION
from nlglib.lexicon.feature.form import (
    BARE_INFINITIVE, SUBJUNCTIVE, GERUND, INFINITIVE, PRESENT_PARTICIPLE,
    PAST_PARTICIPLE, INDICATIVE)
from nlglib.spec.string import StringElement


Verb = namedtuple('Radical', ['radical', 'group'])


class FrenchMorphologyRules(object):

    """Class in charge of performing french morphology rules for any
    type of words: verbs, nouns, determiners, etc.

    """

    a_o_regex = r'(a|ä|à|â|o|ô)'

    @staticmethod
    def get_base_form(element, base_word):
        """Return a word base_form, either from the element or the base word.

        If the element is a verb and the base_word has a base form, or
        if the element has no base form return the base_word base form.
        Else, the base_word base_form is returned.

        """
        if element.category == VERB:
            if base_word and base_word.base_form:
                return base_word.base_form
            else:
                return element.base_form
        else:
            if element.base_form:
                return element.base_form
            elif base_word:
                return base_word.base_form

    @staticmethod
    def replace_element(old_element, new_element_base_form):
        """Return a WordElement which base_form is the argument
        new_element_base_form. This element inherits its category and
        features from the argument old_element.

        Note: the old_element features do not override the new element
        ones, they can only complete them.

        """
        features = old_element.features.copy()
        element = old_element.lexicon.first(
            new_element_base_form,
            category=old_element.category)
        for feature, value in features.items():
            if feature not in element.features:
                element.features[feature] = value
        return element

    @staticmethod
    def feminize_singular_element(element, realised):
        """Return the feminine singular form of the element, or apply
        feminization rules on the argument realization.

        """
        if element.base_form == realised and element.feminine_singular:
            return element.feminine_singular
        elif realised.endswith(('el', 'eil')):
            return '%sle' % realised
        elif realised.endswith('as'):
            return '%sse' % realised
        elif realised.endswith(('en', 'on')):
            return '%sne' % realised
        elif realised.endswith('et'):
            return '%ste' % realised
        elif realised.endswith('eux'):
            return '%sse' % (realised[:-1])
        elif realised.endswith('er'):
            return '%sère' % (realised[:-2])
        elif realised.endswith('eau'):
            return '%selle' % (realised[:-3])
        elif realised.endswith('os'):
            return '%sse' % realised
        elif realised.endswith('gu'):
            return '%së' % realised
        elif realised.endswith('g'):
            return '%sue' % realised
        elif (
                realised.endswith('eur')
                and '%sant' % (realised[:-3]) in element.lexicon.variant_index
        ):
            return '%sse' % (realised[:-1])
        elif realised.endswith('teur'):
            return '%strice' % (realised[:-4])
        elif realised.endswith('if'):
            return '%sve' % (realised[:-1])
        else:
            return '%se' % realised

    @staticmethod
    def pluralize(realised):
        """Return the plural form of the argument realisation string."""
        if realised.endswith(('s', 'x', 'z')):
            return realised
        elif realised.endswith(('au', 'eu')):
            return '%sx' % realised
        elif realised.endswith('al'):
            return '%saux' % (realised[:-2])
        else:
            return '%ss' % realised

    @staticmethod
    def is_pronoun_detached(element):
        """Determine if the argument is detached or not."""
        parent = element.parent

        if parent:
            grandparent = parent.parent
            if parent.discourse_function in (SUBJECT, OBJECT, INDIRECT_OBJECT):
                return True
                #  If the pronoun is in a prepositional phrase,
                #  or it is 1rst or 2nd person and the verb is in imperative
                #  form but not negated, it is detached.
            elif (
                    parent.category == PREPOSITIONAL_PHRASE
                    or element.person in (FIRST, SECOND)
                    or element.reflexive
                    and parent.form == IMPERATIVE
                    and not parent.negated
            ):
                return True
            elif (
                    grandparent.category == PREPOSITIONAL_PHRASE
                    or element.person in (FIRST, SECOND)
                    or element.reflexive
                    and grandparent.form == IMPERATIVE
                    and not grandparent.negated
            ):
                return True
        else:
            # no parent
            return True

        return False

    @staticmethod
    def get_present_radical(base_form, number):
        """Return the radical used in present of the argument regular
        verb element, using the argument number.

        Return a Verb namedtuple with a 'radical' and 'group' attributes.

        """
        # First group verbs, based on 'aimer'
        if base_form.endswith('er'):
            group = 1
            radical = base_form[:-2]
        # Second group verbs, based on voir
        elif base_form.endswith('oir'):
            group = 2
            radical = base_form[:-2]
            if number == PLURAL:
                radical = '%sy' % radical
            else:
                radical = '%si' % radical
        # Second group verbs, based on finir
        elif base_form.endswith('ir'):
            group = 2
            radical = base_form[:-1]
            # if radical.endswith('ï'):
            # for verbs like 'haïr'
            #     radical = '%s%s' % (radical[:-1], 'i')
            if number == PLURAL:
                radical = '%sss' % radical
        elif base_form.endswith('ïr'):
            group = 2
            if number == SINGULAR:
                radical = '%si' % (base_form[:-2])
            else:
                radical = '%sïss' % (base_form[:-2])
        # Third group verbs, based on "vendre" and "mettre"
        elif base_form.endswith('re'):
            group = 3
            radical = base_form[:-2]
            if number == SINGULAR and radical.endswith('t'):
                # remove last 't':
                radical = radical[:-1]
        else:
            raise ValueError('Unrecognized verb group for base form %s' % base_form)
        return Verb(radical, group)

    @staticmethod
    def get_conditional_or_future_radical(element, base_word, base_form):
        """Return the radical used in indicative simple future and
        conditional present of the argument regular verb element, using
        the argument number.

        """
        radical = element.future_radical or base_word.future_radical
        if not radical:
            penultimate_vowel = base_form[-4]
            if base_form.endswith('e'):
                radical = base_form[:-1]
            elif base_form.endswith('yer'):
                radical = '%sier' % (base_form[:-3])
            elif penultimate_vowel in ['e', 'é']:
                radical = '%sè%s' % (base_form[:-4], base_form[-3])
            else:
                radical = base_form
        return radical

    @staticmethod
    def build_verb_past_participle(base_form):
        realised = base_form
        if base_form.endswith('er'):
            realised = '%sé' % (realised[:-2])
        elif base_form.endswith('oir'):
            realised = '%su' % (realised[:-3])
        elif base_form.endswith('ir'):
            realised = realised[:-1]
        elif base_form.endswith('mettre'):
            realised = '%sis' % (realised[:-5])
        elif base_form.endswith('re'):
            realised = '%su' % (realised[:-2])
        return realised

    def add_suffix(self, radical, suffix):
        """Return the concatenation of the radical, any appropriate
        liaison letters and the suffix.

        """
        # change "c" to "ç" and "g" to "ge" before "a" and "o";
        if re.match(self.a_o_regex, suffix):
            if radical.endswith('c'):
                radical = '%s%s' % (radical[:-1], 'ç')
            elif radical.endswith('g'):
                radical = '%s%s' % (radical, 'e')
        # if suffix begins with mute "e"
        elif suffix != 'ez' and suffix.startswith('e'):
            #  change "y" to "i" if not in front of "e"
            if not radical.endswith("ey") and radical.endswith("y"):
                radical = '%s%s' % (radical[:-1], 'i')
            #  change "e" and "é" to "è" in last sillable of radical
            if radical[-2] in ['e', 'é']:
                radical = '%s%s%s' % (radical[:-2], 'é', radical[-1])
        return '%s%s' % (radical, suffix)

    def build_present_verb(self, base_form, person, number):
        """Return the present form for regular verb, using argument
        person and number.

        """
        verb = self.get_present_radical(base_form, number)
        if number in (SINGULAR, BOTH):
            if verb.group == 1:
                if person in (FIRST, THIRD):
                    suffix = 'e'
                else:
                    suffix = 'es'
            elif verb.group == 2:
                if person in (FIRST, SECOND):
                    suffix = 's'
                else:
                    suffix = 't'
            else:  # third group
                if person in (FIRST, SECOND):
                    suffix = 's'
                else:
                    suffix = ''
        else:
            if person == FIRST:
                suffix = 'ons'
            elif person == SECOND:
                suffix = 'ez'
            else:
                suffix = 'ent'
        return self.add_suffix(verb.radical, suffix)

    def build_subjunctive_verb(self, base_form, person, number):
        """Return the subjunctive form for regular verb, using argument
        person and number.

        """
        # Compared to indicative present, singular persons
        # take the radical of third person plural.
        if number == SINGULAR:
            radical_number = PLURAL
        else:
            radical_number = number

        verb = self.get_present_radical(base_form, radical_number)
        if number in (SINGULAR, BOTH):
            if person in (FIRST, THIRD):
                suffix = 'e'
            else:
                suffix = 'es'
        else:
            if person == FIRST:
                suffix = 'ions'
            elif person == SECOND:
                suffix = 'iez'
            else:
                suffix = 'ent'
        return self.add_suffix(verb.radical, suffix)

    def build_future_verb(self, radical, person, number):
        """Return the future form for regular verb, using argument
        person and number.

        """
        if number in (SINGULAR, BOTH):
            if person == FIRST:
                suffix = 'ai'
            elif person == SECOND:
                suffix = 'as'
            else:
                suffix = 'a'
        else:
            if person == FIRST:
                suffix = 'ons'
            elif person == SECOND:
                suffix = 'ez'
            else:
                suffix = 'ont'
        return '%s%s' % (radical, suffix)

    def build_conditional_verb(self, radical, person, number):
        """Return the conditional form for regular verb, using argument
        person and number.

        """
        if number in (SINGULAR, BOTH):
            if person in (FIRST, SECOND):
                suffix = 'ais'
            else:
                suffix = 'ait'
        else:
            if person == FIRST:
                suffix = 'ions'
            elif person == SECOND:
                suffix = 'iez'
            else:
                suffix = 'aient'
        return '%s%s' % (radical, suffix)

    def build_past_verb(self, radical, person, number):
        """Return the past form for regular verb, using argument
        person and number.

        """
        return self.build_conditional_verb(radical, person, number)

    def get_imperfect_pres_part_radical(self, element, base_word, base_form):
        """Gets or builds the radical used for "imparfait" and present participle."""
        if element.imparfait_radical:
            return element.imparfait_radical
        elif base_word.imparfait_radical:
            return base_word.imparfait_radical
        else:
            if element.present1p:
                radical = element.present1p
            elif base_word.present1p:
                radical = base_word.present1p
            else:
                radical = self.build_present_verb(base_form, person=FIRST, number=PLURAL)
            # Remove -ons suffix:
            if radical.endswith('ons'):
                radical = radical[:-3]
            return radical

    def get_verb_parent(self, element):
        """Return the parenf of the verb and its agreement.

        The verb parent can either be its parent or its grandparent,
        or the direct object in the sentence.

        If the returned agreement is True, it means that the parent
        is either a verb phrase, has an object function in the sentence,
        or has either a front/pre/post-modifier function.

        """
        #  Get gender and number from parent or "grandparent" or self, in
        #  that order
        parent = element.parent
        agreement = False
        if element.parent:
            # used as epithet or as attribute of the subject
            if parent.category == VERB_PHRASE or element.discourse_function == OBJECT:
                agreement = True
                if not parent.gender and parent.parent:
                    parent = parent.parent
            else:
                # used as attribute of the direct object
                modifier_functions = [FRONT_MODIFIER, PRE_MODIFIER, POST_MODIFIER]
                if element.discourse_function in modifier_functions:
                    agreement = True
                    for complement in (parent.complements or []):
                        if complement.discourse_function == OBJECT:
                            direct_object = complement
                            parent = direct_object
                            break
        return parent, agreement

    def realise_verb_present_participle_or_gerund(
            self, element, base_word, base_form, gender, number):
        """Realise the verb element which form is either present
        participle or gerund.

        If the verb is regular, the present particple generation rules
        will be used. Else, the present participle will be looked up
        in the lexicon.

        """
        realised = (
            element.present_participle
            or (base_word and base_word.present_participle)
        )
        if not realised:
            radical = self.get_imperfect_pres_part_radical(element, base_word, base_form)
            realised = '%sant' % radical

        #  Note : The gender and number features must only be
        #  passed to the present participle by the syntax when
        #  the present participle is used as an adjective.
        #  Otherwise it is immutable.
        if gender == FEMININE:
            realised = '%se' % realised
        if number == PLURAL:
            realised = '%ss' % realised
        return realised

    def realise_verb_past_participle(
            self, element, base_word, base_form, gender, number):
        """Realise the past participle of the argument verb element.

        The past particple will use the argument gender and number.

        If the verb is regular, the past particple generation rules will
        be used. Else, the (feminine) past participle will be looked up
        in the lexicon.

        """
        realised = (
            element.past_participle
            or (base_word and base_word.past_participle)
        )
        if not realised:
            realised = self.build_verb_past_participle(base_form)

        if gender == FEMININE:
            fem_realised = (
                element.feminine_past_participle
                or (base_word and base_word.feminine_past_participle)
            )
            if not fem_realised:
                realised = '%se' % realised
            else:
                realised = fem_realised
        if number == PLURAL and not realised.endswith('s'):
            realised = '%ss' % realised
        return realised

    def realise_verb_subjunctive(self, element, base_word, base_form, person, number):
        """Realise the subjunctive form of the argument verb element
        at the argument gender and number.

        """
        realised = None
        if number in (SINGULAR, BOTH):
            if person == FIRST:
                realised = (
                    element.subjunctive1s or (base_word and base_word.subjunctive1s))
            elif person == SECOND:
                realised = (
                    element.subjunctive2s or (base_word and base_word.subjunctive2s))
            else:
                realised = (
                    element.subjunctive3s or (base_word and base_word.subjunctive3s))
        else:
            if person == FIRST:
                realised = (
                    element.subjunctive1p or (base_word and base_word.subjunctive1p))
            elif person == SECOND:
                realised = (
                    element.subjunctive2p or (base_word and base_word.subjunctive2p))
            else:
                realised = (
                    element.subjunctive3p or (base_word and base_word.subjunctive3p))
        if not realised:
            realised = self.build_subjunctive_verb(base_form, person, number)
        return realised

    def realise_verb_imperative(self, element, base_word, base_form, person, number):
        """Realise the imperative form of the argument verb element
        at the argument gender and number.

        If the imperative form is not foundin the lexicon

        """
        realised = None
        present_form = self.realise_verb_present(
            element, base_word, base_form, person, number)
        if number in (SINGULAR, BOTH):
            if person in (FIRST, THIRD):
                pass
            else:
                realised = (
                    element.imperative2s
                    or (base_word and base_word.imperative2s)
                    or present_form)
                if realised.endswith('s'):
                    realised = realised[:-1]
        else:
            if person == FIRST:
                realised = (
                    element.imperative1p
                    or (base_word and base_word.imperative1p)
                    or present_form)
            elif person == SECOND:
                realised = (
                    element.imperative2p
                    or (base_word and base_word.imperative2p)
                    or present_form)
        return realised

    def realise_verb_present(self, element, base_word, base_form, person, number):
        """Realise the present form of the argument verb element at the
        argument gender and number.

        If the verb is regular, the present generation rules will
        be used. Else, the appropriate present form will be looked up
        in the lexicon.

        """
        if number in (SINGULAR, BOTH):
            if person == FIRST:
                realised = (element.present1s or (base_word and base_word.present1s))
            elif person == SECOND:
                realised = (element.present2s or (base_word and base_word.present2s))
            else:
                realised = (element.present3s or (base_word and base_word.present3s))
        else:
            if person == FIRST:
                realised = (element.present1p or (base_word and base_word.present1p))
            elif person == SECOND:
                realised = (element.present2p or (base_word and base_word.present2p))
            else:
                realised = (element.present3p or (base_word and base_word.present3p))
        if not realised:
            realised = self.build_present_verb(base_form, person, number)
        return realised

    def morph_determiner(self, element):
        """Perform the morphology for determiners.

        It returns a StringElement made from the baseform, or the plural
        or feminine singular form of the determiner, if it applies.

        """
        parent = element.parent
        if parent and parent.gender:
            gender = parent.gender
        else:
            gender = element.gender

        # plural form
        if (parent and parent.is_plural) or element.is_plural:
            if gender == FEMININE and element.feminine_plural:
                inflected_form = element.feminine_plural
            else:
                inflected_form = element.plural

            # "des" -> "de" in front of noun premodifiers
            if (
                parent
                and inflected_form == "des"
                and parent.premodifiers
            ):
                inflected_form = "de"
        # feminine singular form
        elif gender == FEMININE and element.feminine_singular:
            inflected_form = element.feminine_singular
        # masuculine singular form
        else:
            # remove particle if the determiner has one
            inflected_form = element.base_form.replace(
                element.particle, '').strip()

        return StringElement(string=inflected_form, word=element)

    def morph_adjective(self, element, base_word=None):
        """Performs the morphology for adjectives."""
        base_form = self.get_base_form(element, base_word)
        # Comparatives and superlatives are mainly treated by syntax
        # in French. Only exceptions, provided by the lexicon, are
        # treated by morphology.
        if element.is_comparative:
            realised = element.comparative
            element = self.replace_element(
                old_element=element, new_element_base_form=realised)
            if base_word and not realised:
                realised = base_word.comparative
            if not realised:
                realised = base_form
        else:
            realised = base_form

        #  Get gender from parent or "grandparent" or self, in that order
        discourse_function = element.discourse_function
        parent = element.parent
        if element.parent:
            if element.discourse_function == HEAD:
                discourse_function = parent.discourse_function
            if parent.gender and parent.parent:
                parent = parent.parent
        else:
            parent = element

        # If parent or grandparent is a verb phrase and the adjective is
        # a modifier, assume it's a direct object attribute if there is
        # one.
        if (
                parent.category == VERB_PHRASE and
                discourse_function in [
                    FRONT_MODIFIER, PRE_MODIFIER, POST_MODIFIER]
        ):
            complements = parent.complements
            direct_object = None
            for complement in complements:
                if complement.discourse_function == OBJECT:
                    direct_object = complement
                    break
                if direct_object:
                    parent = direct_object

        #  Feminine
        #  The rules used here apply to the most general cases.
        #  Exceptions are meant to be specified in the lexicon or by the user
        #  by means of the FrenchLexicalFeature.FEMININE_SINGULAR feature.
        if parent.is_feminine or element.is_feminine:
            realised = self.feminize_singular_element(element, realised)

        # Plural
        # The rules used here apply to the most general cases.
        # Exceptions are meant to be specified in the lexicon or by the user
        # by means of the LexicalFeature.PLURAL and
        # FrenchLexicalFeature.FEMININE_PLURAL features.
        if parent.is_plural or element.is_plural:
            if parent.is_feminine or element.is_feminine:
                if element.feminine_plural:
                    realised = element.feminine_plural
                else:
                    realised = '%ss' % realised
            elif element.plural:
                realised = element.plural
            else:
                realised = self.pluralize(realised)

        realised = '%s%s' % (realised, element.particle)

        return StringElement(string=realised, word=element)

    def morph_noun(self, element, base_word=None):
        # The gender of the inflected word is opposite to the base word
        if (
                base_word
                and {base_word.gender, element.gender} == {MASCULINE, FEMININE}
                and base_word.opposite_gender
        ):
            element.base_form = base_word.opposite_gender
            element.base_word = base_word.lexicon.first(element.base_form, category=NOUN)

        base_form = self.get_base_form(element, base_word)
        base_word = element.base_word or base_word

        if (
                (element.parent and element.parent.is_plural
                 or element.is_plural) and not
                element.proper
        ):
            if element.plural and base_word:
                realised = base_word.plural
            else:
                realised = self.pluralize(base_form)
        else:
            realised = base_form

        realised = '%s%s' % (realised, element.particle)
        return StringElement(string=realised, word=element)

    def morph_verb(self, element, base_word):
        """Apply morphology rules for verb words.

        Return a StringElement which realisaton is the morphed verb.

        """
        number = element.number or SINGULAR
        person = element.person or THIRD
        gender = element.gender or MASCULINE
        tense = element.tense or PRESENT
        parent, agreement = self.get_verb_parent(element)
        base_form = self.get_base_form(element, base_word)
        form = element.form or INDICATIVE

        if element.form in [PRESENT_PARTICIPLE, PAST_PARTICIPLE] and agreement:
            gender, number = parent.gender, parent.number

        # The verb morphology depends of its form (infititive, present participle, past
        # participle, etc). Each form has specific morphology rules.
        if form in (BARE_INFINITIVE, INFINITIVE):
            realised = base_form
        elif form in (PRESENT_PARTICIPLE, GERUND):
            realised = self.realise_verb_present_participle_or_gerund(
                element, base_word, base_form, gender, number)
        elif form == PAST_PARTICIPLE:
            realised = self.realise_verb_past_participle(
                element, base_word, base_form, gender, number)
        elif form == SUBJUNCTIVE:
            realised = self.realise_verb_subjunctive(
                element, base_word, base_form, person, number)
        elif form == IMPERATIVE:
            realised = self.realise_verb_imperative(
                element, base_word, base_form, person, number)
        elif tense == PRESENT:
            realised = self.realise_verb_present(
                element, base_word, base_form, person, number)
        elif tense in [CONDITIONAL, FUTURE]:
            radical = self.get_conditional_or_future_radical(element, base_word, base_form)
            if tense == CONDITIONAL:
                realised = self.build_conditional_verb(radical, person, number)
            else:
                realised = self.build_future_verb(radical, person, number)
        elif tense == PAST:
            radical = self.get_imperfect_pres_part_radical(
                element, base_word, base_form)
            realised = self.build_past_verb(radical, person, number)

        realised = '%s%s' % (realised, element.particle)
        return StringElement(string=realised, word=element)

    def morph_adverb(self, element, base_word):
        base_form = self.get_base_form(element, base_word)
        #  Comparatives and superlatives are mainly treated by syntax
        #  in French. Only exceptions, provided by the lexicon, are
        #  treated by morphology.
        if element.is_comparative:
            realised = element.comparative if element.comparative else base_word.comparative
            if not realised:
                realised = base_form
        else:
            realised = base_form

        realised = '%s%s' % (realised, element.particle)
        return StringElement(string=realised, word=element)

    def morph_pronoun(self, element):
        """TODO"""
        #  inflect only personal pronouns, exluding complement pronouns
        # ("y" and "en")
        if element.pronoun_type == PERSONAL and element.discourse_function == COMPLEMENT:
            detached = self.is_pronoun_detached(element)
            gender = element.gender if element.gender != NEUTER else MASCULINE
            passive = element.passive
            parent = element.parent
            person = element.person or THIRD
            features = {
                PRONOUN_TYPE: element.pronoun_type,
                PERSON: person
            }
            number = person.number or SINGULAR
            reflexive = element.reflexive
            func = element.discourse_function
            if not detached and func:
                func = SUBJECT
            if passive:
                if func == SUBJECT:
                    func = OBJECT
                elif func == OBJECT:
                    func = SUBJECT
            if func not in (OBJECT, INDIRECT_OBJECT) and not detached:
                reflexive = False

            # agree the reflexive pronoun with the subject
            if reflexive and parent:
                grandparent = parent.parent
                if grandparent and grandparent.category == VERB_PHRASE:
                    person = grandparent.person
                    number = grandparent.number
                    # If the verb phrase is in imperative form,
                    # the reflexive pronoun can only be in 2S, 1P or 2P
                    if grandparent.form == IMPERATIVE:
                        if person not in (FIRST, SECOND):
                            person = SECOND

            # If the pronoun is the head of a noun phrase,
            # take the discourse function of this noun phrase
            if func == SUBJECT and parent and parent.category == NOUN_PHRASE:
                func = parent.discourse_function

            # select wich features to include in search depending on pronoun
            # features, syntactic function and wether the pronoun is
            # detached from the verb
            if person == THIRD:
                features[REFLEXIVE] = reflexive
                features[DETACHED] = detached
                if not reflexive:
                    features[NUMBER] = number
                    if not detached:
                        features[DISCOURSE_FUNCTION] = func
                        if (
                                (number != PLURAL and func != INDIRECT_OBJECT)
                                or func == SUBJECT
                        ):
                            features[GENDER] = gender
                    else:  # detached
                        features[GENDER] = gender
            else:  # person != THIRD
                features[NUMBER] = number
                if element.is_plural:
                    features[DETACHED] = detached
                    if not detached:
                        if func != SUBJECT:
                            func = None
                        features[DISCOURSE_FUNCTION] = func

            # find appropriate pronoun in lexicon, with the target features
            new_element = element.lexicon.first_word_with_same_features(
                features, category=PRONOUN)
            realised = new_element.base_form

        elif element.PRONOUN_TYPE == RELATIVE:
            #  Get parent clause.
            antecedent = element.parent
            while antecedent and antecedent.category != CLAUSE:
                antecedent = antecedent.parent

            if antecedent:
                # Get parent noun phrase of parent clause.
                # Lookup lexical entry for appropriate form.
                # If the corresponding form is not found :
                # Feminine plural defaults to masculine plural.
                # Feminine singular and masculine plural default
                # to masculine singular.
                if antecedent.feminine and antecedent.plural:
                    realised = antecedent.feminine_plural
                elif antecedent.feminine:
                    realised = antecedent.feminine_singular
                elif antecedent.plural:
                    realised = element.plural

        realised = '%s%s' % (realised, element.particle)
        return StringElement(string=realised, word=element)
