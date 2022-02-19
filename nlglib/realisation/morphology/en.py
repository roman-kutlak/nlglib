"""Definition of English morphology rules.

This package contains the necessary classes for running the
    morphology processor for the English language. It contains the main
    processor plus a syntax class containing some simple morphology rules.
    The best situation is to have a lexicon that handles Inflection. The
    rules given here are only used if the lexicon does not exist or does not
    contain the desired Inflection. As the English language is quite large
    with countless exceptions, the morphology rules contain only the basic
    inflections for words that follow distinct patterns.</p>

The contents of this file are subject to the Mozilla Public
    License Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    https://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS
    IS" basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
    the License for the specific language governing rights and limitations
    under the License.

The Original Code is "Simplenlg".

<P>The Initial Developer of the Original Code is Ehud Reiter, Albert
    Gatt and Dave Westwater. Portions created by Ehud Reiter, Albert Gatt
    and Dave Westwater are Copyright (C) 2010-11 The University of Aberdeen.
    All Rights Reserved.</P>

<P>Contributor(s): Ehud Reiter, Albert Gatt, Dave Wewstwater, Roman
    Kutlak, Margaret Mitchell.</P>

"""


import enum
import re

from nlglib.lexicon import feature
from nlglib.lexicon.feature import category, form, tense, gender
from nlglib.lexicon.feature import discourse
from nlglib.lexicon.feature import internal
from nlglib.lexicon.feature import lexical
from nlglib.lexicon.feature import number
from nlglib.lexicon.feature import person
from nlglib.lexicon.feature import pronoun  # noqa
from nlglib.spec.string import StringElement


# INFLECTIONS
class Inflection(enum.Enum):
    REGULAR = 'reg'
    IRREGULAR = 'irreg'
    REGULAR_DOUBLE = 'regd'
    GRECO_LATIN_REGULAR = 'glreg'
    UNCOUNT = 'uncount'
    INVARIANT = 'inv'

    @classmethod
    def _missing_(cls, value):
        if value in ('uncount', 'noncount', 'groupuncount'):
            return Inflection.UNCOUNT
        if value is None:
            return None
        super()._missing_(value)


WORD_ENDS_WITH_VOWEL_RE = re.compile(r".*[^aeiou]y$")
CONSONANT_RE = re.compile(r'[^aeiou]')
CONSONANTS_RE = re.compile(r'[^aeiou]+')
VOWEL_RE = re.compile(r'[aeiou]')
VOWELS_RE = re.compile(r'[aeiou]+')
ENDS_WITH_VOWEL_RE = re.compile(r'.*[aeiou]$')

PRONOUNS = {
    number.SINGULAR: {
        discourse.SUBJECT: {
            person.FIRST: "I",
            person.SECOND: "you",
            person.THIRD: {
                gender.MASCULINE: "he",
                gender.FEMININE: "she",
                gender.NEUTER: "it",
            }
        },
        discourse.OBJECT: {
            person.FIRST: "me",
            person.SECOND: "you",
            person.THIRD: {
                gender.MASCULINE: "him",
                gender.FEMININE: "her",
                gender.NEUTER: "it",
            }
        },
        discourse.SPECIFIER: {
            person.FIRST: "my",
            person.SECOND: "your",
            person.THIRD: {
                gender.MASCULINE: "his",
                gender.FEMININE: "her",
                gender.NEUTER: "its",
            }
        },
        lexical.REFLEXIVE: {
            person.FIRST: "myself",
            person.SECOND: "yourself",
            person.THIRD: {
                gender.MASCULINE: "himself",
                gender.FEMININE: "herself",
                gender.NEUTER: "itself",
            }
        },
        feature.POSSESSIVE: {
            person.FIRST: "mine",
            person.SECOND: "yours",
            person.THIRD: {
                gender.MASCULINE: "his",
                gender.FEMININE: "hers",
                gender.NEUTER: "its",
            },
        },
    },
    number.PLURAL: {
        discourse.SUBJECT: {
            person.FIRST: "we",
            person.SECOND: "you",
            person.THIRD: {
                gender.MASCULINE: "they",
                gender.FEMININE: "they",
                gender.NEUTER: "they",
            }
        },
        discourse.OBJECT: {
            person.FIRST: "us",
            person.SECOND: "you",
            person.THIRD: {
                gender.MASCULINE: "them",
                gender.FEMININE: "them",
                gender.NEUTER: "them",
            }
        },
        discourse.SPECIFIER: {
            person.FIRST: "our",
            person.SECOND: "your",
            person.THIRD: {
                gender.MASCULINE: "their",
                gender.FEMININE: "their",
                gender.NEUTER: "their",
            }
        },
        lexical.REFLEXIVE: {
            person.FIRST: "ourselves",
            person.SECOND: "yourselves",
            person.THIRD: {
                gender.MASCULINE: "themselves",
                gender.FEMININE: "themselves",
                gender.NEUTER: "themselves",
            }
        },
        feature.POSSESSIVE: {
            person.FIRST: "ours",
            person.SECOND: "yours",
            person.THIRD: {
                gender.MASCULINE: "theirs",
                gender.FEMININE: "theirs",
                gender.NEUTER: "theirs",
            }
        },
    },
    number.BOTH: "both"
}


WH_PRONOUNS = {"who", "what", "which", "where", "why", "how", "how many"}


class EnglishMorphologyRules(object):

    """Class in charge of performing English morphology rules for any
    type of words: verbs, nouns, determiners, etc.

    """

    @staticmethod
    def get_base_form(element, base_word):
        """Return a word base_form, either from the element or the base word.

        If the element is a verb and the base_word has a base form, or
        if the element has no base form return the base_word base form.
        Else, the base_word base_form is returned.

        """
        if element.category == category.VERB:
            if base_word and base_word.base_form:
                return base_word.base_form
            else:
                return element.base_form
        else:
            if element.base_form:
                return element.base_form
            elif base_word:
                return base_word.base_form

    def morph_adjective(self, element, base_word=None):
        """Perform the morphology for adjectives."""
        base_word = element.base_word or base_word
        base_form = self.get_base_form(element, base_word)
        pattern_value = element.default_infl

        if element.is_comparative:
            if element.comparative:
                realised = element.comparative
            elif base_word and base_word.comparative:
                realised = base_word.comparative
            else:
                if pattern_value == 'glreg':  # regular doubling form; big/bigger
                    realised = build_double_comparative(base_form)
                else:
                    realised = build_regular_comparative(base_form)
        elif element.is_superlative:
            realised = element.superlative
            if not realised and base_word:
                realised = base_word.superlative
            if not realised:
                if pattern_value == 'glreg':  # regular doubling form; big/biggest
                    realised = build_double_superlative(base_form)
                else:
                    realised = build_regular_superlative(base_form)
        else:
            realised = base_form
        # NOTE: simplenlg copies over just DISCOURSE_FUNCTION feature
        return StringElement(string=realised, word=element)

    def morph_adverb(self, element, base_word=None):
        """Perform the morphology for adverbs."""
        base_word = element.base_word or base_word
        base_form = self.get_base_form(element, base_word)

        if element.is_comparative:
            if element.comparative:
                realised = element.comparative
            elif base_word and base_word.comparative:
                realised = base_word.comparative
            else:
                if base_form.endswith('ly'):
                    realised = 'more ' + base_form
                else:
                    realised = build_regular_comparative(base_form)
        elif element.is_superlative:
            if element.superlative:
                realised = element.superlative
            elif base_word and base_word.superlative:
                realised = base_word.superlative
            else:
                if base_form.endswith('ly'):
                    realised = 'most ' + base_form
                else:
                    realised = build_regular_superlative(base_form)
        else:
            realised = base_form
        # NOTE: simplenlg copies over just DISCOURSE_FUNCTION feature
        return StringElement(string=realised, word=element)

    def morph_determiner(self, element, np_realisation=None):
        # NOTE: implementation differs from SimpleNLG: it doesn't require np_realisation
        rv = StringElement(string=element.base_form, word=element)
        if element.is_plural:
            if element.realisation == 'that':
                rv = StringElement(string='those', word=element)
            if element.realisation == 'this':
                rv = StringElement(string='these', word=element)
        else:
            if element.realisation == 'those':
                rv = StringElement(string='that', word=element)
            if element.realisation == 'these':
                rv = StringElement(string='this', word=element)

        # Special "a" determiner
        helper = DeterminerAgrHelper()
        if rv.realisation in ('a', 'an'):
            if rv.is_plural:
                rv.realisation = 'some'
            elif np_realisation and helper.requires_an(np_realisation):
                rv.realisation = 'an'
        return rv

    def morph_noun(self, element, base_word=None):
        """This method performs the morphology for nouns.
        @param element  the `InflectedWordElement`.
        @param base_word the `WordElement` as created from the lexicon entry.
        @return a `StringElement` representing the word after Inflection.
        """
        base_form = self.get_base_form(element, base_word)
        base_word = element.base_word or base_word

        if not element.proper and (element.is_plural or element.parent and element.parent.is_plural):

            if element.default_infl == "uncount":
                plural_form = base_form
            else:
                plural_form = element.plural

            if plural_form is None and base_word is not None:
                if base_word.default_infl == "uncount":
                    plural_form = base_form
                else:
                    plural_form = base_word.plural

            # INFL_CODES: nlglib/lexicon/lexicon.py:38
            if plural_form is None:
                if element.default_infl == "glreg":
                    plural_form = build_greco_latin_plural_noun(base_form)
                else:
                    plural_form = build_regular_plural_noun(base_form)

            realised = plural_form
        else:
            realised = base_form

        if element.possessive:
            if realised[-1] == "s":
                realised += "'"
            else:
                realised += "'s"

        return StringElement(string=realised, word=element)

    def morph_pronoun(self, element):
        if element.features.get(internal.NON_MORPH):
            realised = element.base_form
        elif is_wh_pronoun(element):
            realised = element.base_form
        else:
            gender_value = element.gender or gender.NEUTER
            person_value = element.person or person.FIRST
            number_value = element.number or number.SINGULAR
            discourse_value = element.discourse_function or discourse.SUBJECT
            is_passive = element.passive if element.passive is not None else False
            is_specifier = discourse_value == discourse.SPECIFIER
            is_possessive = element.possessive
            is_reflexive = element.reflexive
            as_subject = (
                (discourse_value == discourse.SUBJECT and not is_passive) or
                (discourse_value == discourse.OBJECT and is_passive) or
                (discourse_value == discourse.COMPLEMENT and is_passive) or
                is_specifier
            )
            as_object = not as_subject

            if is_reflexive:
                use = lexical.REFLEXIVE
            elif is_possessive:
                use = discourse.SPECIFIER if is_specifier else feature.POSSESSIVE
            else:
                if as_subject:
                    use = discourse.SUBJECT
                elif as_object:
                    use = discourse.OBJECT
                else:
                    use = discourse.SUBJECT

            lookup = PRONOUNS.get(number_value, {}).get(use, {}).get(person_value)
            if person_value == person.THIRD and lookup:
                lookup = lookup.get(gender_value)

            realised = lookup or element.base_form

        return StringElement(string=realised, word=element)

    def morph_verb(self, element, base_word):
        """This method performs the morphology for verbs.

        @param element  the `InflectedWordElement`.
        @param base_word the `WordElement` as created from the lexicon entry.
        @return a `StringElement` representing the word after
        Inflection."""
        number_value = element.number
        person_value = element.person
        tense_value = element.tense

        form_value = element.form
        pattern_value = Inflection(element.default_infl)

        base_form = self.get_base_form(element, base_word)
        base_form_is_be = base_form and base_form.lower() == "be"

        if element.negated or form_value == form.BARE_INFINITIVE:
            realised = base_form

        elif element.form == form.IMPERATIVE:
            realised = base_form

        elif form_value == form.PRESENT_PARTICIPLE:
            realised = element.present_participle

            if realised is None and base_word is not None:
                realised = base_word.present_participle

            if realised is None:
                if Inflection.REGULAR_DOUBLE == pattern_value:
                    realised = build_double_present_participle_verb(base_form)
                else:
                    realised = build_regular_present_participle_verb(base_form)

        elif tense.PAST == tense_value or form.PAST_PARTICIPLE == form_value:

            if form_value == form.PAST_PARTICIPLE:
                realised = element.features.get(lexical.PAST_PARTICIPLE)

                if realised is None and base_word is not None:
                    realised = base_word.features.get(lexical.PAST_PARTICIPLE)

                if realised is None:
                    if base_form_is_be:
                        realised = "been"
                    elif pattern_value == Inflection.REGULAR_DOUBLE:
                        realised = build_double_past_verb(base_form)
                    else:
                        realised = build_regular_past_verb(base_form, number_value, person_value)

            else:
                realised = element.features.get(lexical.PAST)

                if realised is None and base_word is not None:
                    realised = base_word.features.get(lexical.PAST)

                if realised is None:
                    if pattern_value == Inflection.REGULAR_DOUBLE:
                        realised = build_double_past_verb(base_form)
                    else:
                        realised = build_regular_past_verb(base_form, number_value, person_value)

        elif (
            (number_value is None or number_value == number.SINGULAR)
            and (person_value is None or person_value == person.THIRD)
            and (tense_value is None or tense_value == tense.PRESENT)
        ):

            realised = element.features.get(lexical.PRESENT3S)

            if realised is None and base_word is not None and base_form_is_be:
                realised = base_word.features.get(lexical.PRESENT3S)

            if realised is None:
                realised = build_present_3s_verb(base_form)

        else:
            if base_form_is_be:
                if person_value == person.FIRST and (number_value == number.SINGULAR or number_value is None):
                    realised = "am"
                else:
                    realised = "are"
            else:
                realised = base_form

        return StringElement(string=realised or base_form, word=element)


def build_regular_plural_noun(base_form: str):
    """Build a plural for regular nouns.

    The rules are performed in this order:
    * For nouns ending "-Cy", where C is any consonant, the ending
    becomes "-ies". For example, "fly" becomes "flies".
    * For nouns ending "-ch", "-s", "-sh", "-x"
    or "-z" the ending becomes "-es". For example, "box"
    becomes "boxes".
    * All other nouns have "-s" appended the other end. For example,
    "dog" becomes "dogs".

    @param base_form the base form of the word.
    @return the inflected word.
    """
    plural = None
    if base_form is not None:
        if re.match(r".*[b-zand[^eiou]]y\b", base_form):
            plural = re.sub(r"y\b", "ies", base_form)
        elif re.match(r".*([szx]|[cs]h)\b", base_form):
            plural = base_form + "es"
        else:
            plural = base_form + "s"

    return plural


def build_greco_latin_plural_noun(base_form: str) -> str:
    """Build a plural for Greco-Latin regular nouns.

    The rules are performed in this order:
    * For nouns ending "-us" the ending becomes "-i". For
    example, "focus" becomes "foci".
    * For nouns ending "-ma" the ending becomes "-mata". For
    example, "trauma" becomes "traumata".
    * For nouns ending "-a" the ending becomes "-ae". For
    example, "larva" becomes "larvae".
    * For nouns ending "-um" or "-on" the ending becomes
    "-a". For example, "taxon" becomes "taxa".
    * For nouns ending "-sis" the ending becomes "-ses". For
    example, "analysis" becomes "analyses".
    * For nouns ending "-is" the ending becomes "-ides". For
    example, "cystis" becomes "cystides".
    * For nouns ending "-men" the ending becomes "-mina". For
    example, "foramen" becomes "foramina".
    * For nouns ending "-ex" the ending becomes "-ices". For
    example, "index" becomes "indices".
    * For nouns ending "-x" the ending becomes "-ces". For
    example, "matrix" becomes "matrices".

    @param base_form the base form of the word.
    @return the inflected word.
    """
    plural = None
    if base_form is not None:
        if base_form.endswith("us"):
            plural = re.sub(r"us\b", "i", base_form)
        elif base_form.endswith("ma"):
            plural = base_form + "ta"
        elif base_form.endswith("a"):
            plural = base_form + "e"
        elif base_form.endswith("um"):
            plural = re.sub(r"um\b", "a", base_form)
        elif base_form.endswith("on"):
            plural = re.sub(r"on\b", "a", base_form)
        elif base_form.endswith("sis"):
            plural = re.sub(r"sis\b", "ses", base_form)
        elif base_form.endswith("is"):
            plural = re.sub(r"is\b", "ides", base_form)
        elif base_form.endswith("men"):
            plural = re.sub(r"men\b", "mina", base_form)
        elif base_form.endswith("ex"):
            plural = re.sub(r"ex\b", "ices", base_form)
        elif base_form.endswith("x"):
            plural = re.sub(r"x\b", "ces", base_form)
        else:
            plural = base_form

    return plural


def build_double_comparative(base_form):
    """Build the comparative form for adjectives that follow the doubling form
    of the last consonant.

    "-er" is added to the end after the last consonant is doubled.
    For example, "fat" becomes "fatter".

    Args:
         base_form: the base form of the word.
    Returns:
         the inflected word

    """
    morphology = None
    if base_form:
        morphology = base_form + base_form[-1] + "er"
    return morphology


def build_regular_comparative(base_form):
    """Build the comparative form for regular adjectives.

    The rules are performed in this order:

    * adjectives with 2 and more syllables are returned with 'more'
    * For adjectives ending "-Cy", where C is any consonant, the
    ending becomes "-ier". For example, "brainy" becomes
    "brainier".
    * For adjectives ending "-e" the ending becomes "-er".
    For example, "fine" becomes "finer".
    * For all other adjectives, "-er" is added to the end. For
    example, "clear" becomes "clearer".


    Technically many disyllable words can take both forms but we are being
    cautious and use 'more'; you can add the word to the lexicon to avoid this.

    For example, 'fine' is in the english lexicon so it is realised
    as 'finest' instead of 'more fine'.

    Args:
         base_form: the base form of the word.
    Returns:
         the inflected word

    """
    morphology = None
    if base_form:
        num_syllables = count_syllables(base_form)
        if num_syllables >= 2:
            return 'more ' + base_form
        if WORD_ENDS_WITH_VOWEL_RE.match(base_form):
            morphology = re.sub(r"y\b", "ier", base_form)
        elif base_form.endswith("e"):
            morphology = base_form + "r"
        else:
            morphology = base_form + "er"
    return morphology


def build_double_superlative(base_form):
    """Build the superlative form for adjectives that follow the doubling form
    of the last consonant.

    "-er" is added to the end after the last consonant is doubled.
    For example, "fat" becomes "fattest".

    Args:
         base_form: the base form of the word.
    Returns:
         the inflected word

    """
    morphology = None
    if base_form:
        morphology = base_form + base_form[-1] + "est"
    return morphology


def build_regular_superlative(base_form):
    """Build the superlative form for regular adjectives.

    The rules are performed in this order:

    * adjectives with 2 and more syllables are returned with 'most'
    * For adjectives ending "-Cy", where C is any consonant, the
    ending becomes "-iest". For example, "brainy" becomes
    "brainiest".
    * For adjectives ending "-e" the ending becomes "-est".
    For example, "fine" becomes "finest".
    * For all other adjectives, "-est" is added to the end. For
    example, "clear" becomes "clearest".


    Similarly to comparative, many disyllable adjectives can be used
    with 'most' or can be morphed; you can add the word to the lexicon
    to avoid using 'most'.

    For example, 'fine' is in the english lexicon so it is realised
    as 'finest' instead of 'more fine'.

    Args:
         base_form: the base form of the word.
    Returns:
         the inflected word

    """
    morphology = None
    if base_form:
        num_syllables = count_syllables(base_form)
        if num_syllables >= 2:
            return 'most ' + base_form
        if WORD_ENDS_WITH_VOWEL_RE.match(base_form):
            morphology = re.sub(r"y\b", "iest", base_form)
        elif base_form.endswith("e"):
            morphology = base_form + "st"
        else:
            morphology = base_form + "est"
    return morphology


def count_syllables(wordform):
    """Return the estimated number of syllables in a wordform."""
    # if wordform contains *, replace it with x so we don't mix them
    wordform = wordform.replace('*', 'x')
    # replace vowel groups with *
    vowel_groups = re.sub(VOWELS_RE, '*', wordform)
    ends_with_vowel = int(bool(ENDS_WITH_VOWEL_RE.match(wordform)))
    num_syllables = vowel_groups.count('*') - ends_with_vowel
    # if there is only one vowel group and it is at the end return 1 instead of 0
    return max(1, num_syllables)


def is_wh_pronoun(wordform):
    return wordform in WH_PRONOUNS


class DeterminerAgrHelper:
    """This class is used to parse numbers that are passed as figures, to determine
    whether they should take "a" or "an" as determiner.
    """

    # An array of strings which are exceptions to the rule that "an" comes before vowels
    AN_EXCEPTIONS = {"one", "180", "110"}

    # Start of string involving vowels, for use of "an"
    AN_AGREEMENT = re.compile(r"\A([aeiou]).*")

    # Start of string involving numbers, for use of "an" -- courtesy of Chris Howell, Agfa healthcare corporation
    AN_NUMERAL_AGREEMENT = re.compile(r"^(((8((\d+)|(\d+([.,])\d+))?).*)|((11|18)(\d{3,}|\D)).*)$")

    NUMBERS_WITH_VOWEL_SOUND = re.compile("^(8|11|18).*$")

    def requires_an(self, string):
        """
        Check whether this string starts with a number that needs "an" (e.g. "an 18% increase")
        @param string the string
        @return `True` if this string starts with 11, 18, or 8,
        excluding strings that start with 180 or 110
        """
        req = False

        lowercase_input = string.lower()

        if self.AN_AGREEMENT.match(lowercase_input) and not self.is_an_exception(lowercase_input):
            req = True

        else:
            num_pref = self.get_numeric_prefix(lowercase_input)

            if num_pref and len(num_pref) > 0 and self.NUMBERS_WITH_VOWEL_SOUND.match(num_pref):
                num = int(num_pref)
                req = self.check_num(num)

        return req

    def is_an_exception(self, string):
        """Check whether a string beginning with a vowel is an exception and doesn't
        take "an" (e.g. "a one percent change")
        """
        return string and any(string.startswith(exception) for exception in self.AN_EXCEPTIONS)

    def check_num(self, num):
        """Return `True` if the number starts with 8, 11 or 18 and is
        either less than 100 or greater than 1000, but excluding 180,000 etc.
        """
        needs_an = False

        # eight, eleven, eighty and eighteen
        if num == 11 or num == 18 or num == 8 or (80 <= num < 90):
            needs_an = True
        elif num > 1000:
            num = round(num / 1000)
            needs_an = self.check_num(num)

        return needs_an

    def get_numeric_prefix(self, string):
        """Retrieve the numeral prefix of a string"""

        if not (string or string.strip()):
            return None

        string = string.strip()
        numeric = []

        allowed_chars = {str(n) for n in range(10)} | {".", ","}

        for char in string:
            if char not in allowed_chars:
                break
            if char.isdigit():
                numeric.append(char)

        return "".join(numeric) if numeric else None

    def check_ends_with_indefinite_article(self, text: str, np: str):
        """Check to see if a string ends with the indefinite article "a" and it agrees with :@code np}.
        @return an altered version of :@code text} to use "an" if it agrees with :@code np}, the
        original string otherwise.
        """
        tokens = text.split(" ")
        if not tokens:
            return text

        last_token = tokens[-1]

        if last_token.lower() == "a" and self.requires_an(np):
            tokens[-1] = "an"
            return " ".join(tokens)

        # NOTE: SimpleNLG doesn't handle this; is there a reason?
        if last_token.lower() == "an" and not self.requires_an(np):
            tokens[-1] = "a"
            return " ".join(tokens)

        return text


def build_present_3s_verb(base_form):
    """Builds the third-person singular form for regular verbs. The rules are
    performed in this order:
    
    * If the verb is "be" the realised form is "is".
    * For verbs ending "-ch", "-s", "-sh", "-x"
    or "-z" the ending becomes "-es". For example,
    "preach" becomes "preaches".
    * For verbs ending "-y" the ending becomes "-ies". For
    example, "fly" becomes "flies".
    * For every other verb, "-s" is added to the end of the word.
    

    @param base_form the base form of the word.
    @return the inflected word.
    """
    morphology = None
    base_form = base_form and base_form.lower()
    if base_form is not None:
        if base_form == "be":
            morphology = "is"
        elif re.match(r".#[szx]|(ch)|(sh)\b", base_form):
            morphology = base_form + "es"
        elif re.match(r".#[b-zand[^eiou]]y\b", base_form):
            morphology = re.sub(r"y\b", "ies", base_form)
        else:
            morphology = base_form + "s"
    return morphology


def build_regular_past_verb(base_form, number_value, person_value):
    """Builds the past-tense form for regular verbs. The rules are performed in
    this order:
    
    * If the verb is "be" and the number agreement is plural then
    the realised form is "were".
    * If the verb is "be" and the number agreement is singular then
    the realised form is "was", unless the person is second, in which
    case it's "were".
    * For verbs ending "-e" the ending becomes "-ed". For
    example, "chased" becomes "chased".
    * For verbs ending "-Cy", where C is any consonant, the ending
    becomes "-ied". For example, "dry" becomes "dried".
    * For every other verb, "-ed" is added to the end of the word.
    

    @param base_form the base form of the word.
    @param number_value   the number agreement for the word.
    @param person_value   the person
    @return the inflected word.
    """
    morphology = None
    base_form = base_form and base_form.lower()
    if base_form is not None:
        if base_form == "be":
            if number_value == number.PLURAL:
                morphology = "were"
            elif person_value == person.SECOND:
                morphology = "were"
            else:
                morphology = "was"
        elif base_form.endswith("e"):
            morphology = base_form + "d"
        elif re.match(r".#[b-zand[^eiou]]y\b", base_form):
            morphology = re.sub(r"y\b", "ied", base_form)
        else:
            morphology = base_form + "ed"
    return morphology


def build_double_past_verb(base_form):
    """Builds the past-tense form for verbs that follow the doubling form of the
    last consonant. "-ed" is added to the end after the last consonant
    is doubled. For example, "tug" becomes "tugged".

    @param base_form the base form of the word.
    @return the inflected word.
    """
    morphology = None
    if base_form is not None:
        morphology = base_form + base_form[-1] + "ed"
    return morphology


def build_regular_present_participle_verb(base_form):
    """Builds the present participle form for regular verbs. The rules are
    performed in this order:
    
    * If the verb is "be" then the realised form is "being".
    * For verbs ending "-ie" the ending becomes "-ying". For
    example, "tie" becomes "tying".
    * For verbs ending "-ee", "-oe" or "-ye" then
    "-ing" is added to the end. For example, "canoe" becomes
    "canoeing".
    * For other verbs ending in "-e" the ending becomes
    "-ing". For example, "chase" becomes "chasing".
    * For all other verbs, "-ing" is added to the end. For example,
    "dry" becomes "drying".
    

    @param base_form the base form of the word.
    @return the inflected word.
    """
    morphology = None
    base_form = base_form and base_form.lower()
    if base_form is not None:
        if base_form == "be":
            morphology = "being"
        elif base_form.endswith("ie"):
            morphology = re.sub(r"ie\b", "ying", base_form)
        elif re.match(r".#[^iyeo]e\b", base_form):
            morphology = re.sub(r"e\b", "ing", base_form)
        else:
            morphology = base_form + "ing"
    return morphology


def build_double_present_participle_verb(base_form):
    """Builds the present participle form for verbs that follow the doubling
    form of the last consonant. "-ing" is added to the end after the
    last consonant is doubled. For example, "tug" becomes
    "tugging".

    @param base_form the base form of the word.
    @return the inflected word.
    """
    morphology = None
    if base_form is not None:
        morphology = base_form + base_form[-1] + "ing"
    return morphology
