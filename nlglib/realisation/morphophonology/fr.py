# encoding: utf-8

"""Definition of the french morphophonologic rules.

References :
Grevisse, Maurice (1993). Le bon usage, grammaire française, 12e édition
refondue par André Goosse, 8e tirage, Éditions Duculot, Louvain-la-Neuve,
Belgique.

"""


import re

from nlglib.spec.word import InflectedWordElement
from nlglib.lexicon.feature import internal as internal_features
from nlglib.lexicon.feature import lexical as lexical_features
from nlglib.lexicon.feature import category
from nlglib.lexicon.feature import pronoun
from nlglib.lexicon.feature import person
from nlglib.lexicon.feature.number import SINGULAR
from nlglib.lexicon.feature import ELIDED
from nlglib.lexicon.feature.gender import FEMININE
from nlglib.lexicon.feature.lexical import PRONOUN_TYPE
from nlglib.lexicon.feature.lexical.fr import DETACHED

# noinspection RegExpSingleCharAlternation
VOWELS_RE = re.compile(
    r'a|A|ä|Ä|à|À|â|Â|'
    r'e|E|ë|Ë|é|É|è|È|ê|Ê|'
    r'i|I|ï|Ï|î|Î|'
    r'o|O|ô|Ô|'
    r'u|U|û|Û|ü|Ü|ù|Ù|'
    r'y|Y|ý|Ý|ÿ|Ÿ|'
    r'h|H')  # special case of aspired h

# Matches le, les, lequel, lesquel, lesquelles
LE_LEQUEL_RE = re.compile(r'le(quel)?')
LES_LESQUELS_RE = re.compile(r'les(quel(le)?s)?')


def match(pattern, word):
    return re.match(pattern, word.realisation)


def search(pattern, word):
    return re.search(pattern, word.realisation)


def start_with_vowel(word):
    """Return True if the word realisation starts with a vowel.

    A word can be marked as having a so-called "aspired h"
    even if it isn't written with an "h" at the beginning.
    Numerals are also considered to have this trait.
    ("le onzième jour", "le huit du mois")

    """
    return (
        bool(re.match(VOWELS_RE, word.realisation[0]))
        and not word.aspired_h
        and not word.realisation.endswith('ième'))


def _bind_words(
        left_word, right_word,
        left_pattern, singular_right_pattern, plural_right_pattern,
        singular_replacement, plural_remplacement):
    """Join the left and right words by modifying their representation,
    only if the left_pattern matches the left word representation, the
    right pattern matches the right_word representation.

    Depending on the numerality of the match (singular or plural),
    the singular_replacement or plural_remplacement will be used to
    join the two words.

    """
    left_match = search(left_pattern, left_word)
    if not left_match:
        return

    if match(plural_right_pattern, right_word):
        left_word.realisation = (
            left_word.realisation[:-len(left_match.group())] +
            plural_remplacement +
            right_word.realisation[len(plural_remplacement):])
        right_word.realisation = None
    elif match(singular_right_pattern, right_word):
        left_word.realisation = (
            left_word.realisation[:-len(left_match.group())] +
            singular_replacement +
            right_word.realisation[len(singular_replacement):])
        right_word.realisation = None


def replace_de_le_by_du(left_word, right_word):
    """If the left word starts or ends with (or is) 'de' and the right
    word starts with 'le' (or 'lequel'), replace everything by 'du'.

    If the right word starts with 'les' or 'lesquels', replace everything
    by 'des'.

    If not, do nothing.

    """
    _bind_words(
        left_word, right_word,
        left_pattern=r'de$',
        singular_right_pattern=LE_LEQUEL_RE,
        singular_replacement='du',
        plural_right_pattern=LES_LESQUELS_RE,
        plural_remplacement='des')


def replace_a_le_by_au(left_word, right_word):
    """If the left word starts or ends with (or is) 'à' and the right
    word starts with 'le' (or 'lequel'), join the two words by 'au'.

    If the right word starts with 'les' or 'lesquels', join the two
    words by 'aux'.

    If not, do nothing.

    """
    _bind_words(
        left_word, right_word,
        left_pattern=r'à$',
        singular_right_pattern=LE_LEQUEL_RE,
        singular_replacement='au',
        plural_right_pattern=LES_LESQUELS_RE,
        plural_remplacement='aux')


def insert_au_du(left_word, right_word):
    if (
        left_word.category in [category.PREPOSITION, category.COMPLEMENTISER]
        and (right_word.category == category.DETERMINER
             or right_word.pronoun_type == pronoun.RELATIVE)
    ):
        replace_de_le_by_du(left_word, right_word)
        replace_a_le_by_au(left_word, right_word)
        return True


def undetach_pronoun(left_word, right_word):
    if (
            left_word.base_word
            and left_word.category == category.PRONOUN
            and left_word.person in [person.FIRST, person.SECOND]
            and left_word[PRONOUN_TYPE] == pronoun.PERSONAL
            and left_word.number == SINGULAR
            and left_word[DETACHED]
            and right_word.category == category.PRONOUN
            and right_word[PRONOUN_TYPE] == pronoun.SPECIAL_PERSONAL
    ):
        base_word = left_word.base_word
        base_word[DETACHED] = False
        del base_word[lexical_features.DEFAULT_INFL]
        del base_word[lexical_features.INFLECTIONS]
        base_word[internal_features.DISCOURSE_FUNCTION] = None
        new_base_word = base_word.lexicon.first_word_with_same_features(
            category=base_word.category, features=base_word.features)
        if new_base_word:
            inflected_new_base_word = InflectedWordElement(word=new_base_word)
            left_word.features = inflected_new_base_word.features.copy()
            left_word.category = inflected_new_base_word.category
            left_word[ELIDED] = False
            left_word.realisation = new_base_word.base_form
            return True


def add_apostrophe(left_word, right_word):
    """Add an apostrophe between the left and right word, if needed.

    Two cases are identified:
    1 - si + ils → s'ils
    2 - left word is a singular word, ending with an elided vowel
    (or by 'de' or 'que') and the first letter of the right word is a
    vowel.

    Examples for case 2:
    - que + ils → qu'ils
    - le + arbre → l'arbre

    If these cases, the last letter (a vowel) of the left word will
    be removed, and replaced by an apostrophe.

    """
    si_ils_elision = match(r' ?si', left_word) and match(r'il(s)?', right_word)
    contiguous_vowels_elision = (
        (
            (left_word.vowel_elision and not left_word.is_plural)
            or left_word.realisation.endswith((' de', ' que'))
        ) and start_with_vowel(right_word))
    if si_ils_elision or contiguous_vowels_elision:
        # Remove last letter (vowel) of left word and append an
        # apostrophe. The orthography processing will later make sure
        # that no space is put after the apostrophe
        left_word.realisation = left_word.realisation[:-1] + "'"
        return True


def replace_word_by_liaison_form(left_word, right_word):
    if (
            left_word.parent
            and left_word.category in [category.DETERMINER or category.ADJECTIVE]
            and left_word.liaison
    ):
        # Get gender from parent or "grand-parent" for adjectives
        if not left_word.parent.gender and left_word.parent.parent:
            left_word.parent = left_word.parent.parent

        # adjectives which have a different form in front of a vowel
        # when masculine singular,
        # possessive determiners when feminine singular
        # and non possessive determiners when masculine singular
        feminine = left_word.parent.gender == FEMININE
        if (
                start_with_vowel(right_word)
                and not left_word.parent.is_plural
                and ((
                    left_word.category == category.DETERMINER
                    and left_word.possessive == feminine
                ) or
                    (
                        left_word.category == category.ADJECTIVE
                        and right_word.category == category.NOUN
                        and not feminine))):

            left_word.realisation = left_word.liaison
            return True


def deduplicate_left_right_realisation(left_word, right_word):
    """Remove the right word realisation if it's a duplicate of the left one."""
    if (
        (
            left_word.realisation == 'de'
            and right_word.realisation in ['de', 'du', "d'"]
        )
        or (
            left_word.realisation == 'que'
            and right_word.realisation in ['que', "qu'"]
        )
    ):
        right_word.realisation = None
        return True


def apply_rules(left_word, right_word):
    """Apply french morphophonologic rules to make sure that the
    transition between the left and right word is grammatically correct.

    """
    if not left_word.realisation and right_word.realisation:
        return

    # Replace de + le by du, and associated rules
    if insert_au_du(left_word, right_word):
        return
    # special rule with "en" and "y" : the personal pronoun immediately
    # preceding it takes non detached form even if it is attached to an
    # imperative verb
    if undetach_pronoun(left_word, right_word):
        return

    # words who have their last vowel elided and take an apostrophe
    # when in front of a vowel (and singular for determiners)
    if add_apostrophe(left_word, right_word):
        return

    # Remove right duplication if it's a duplicate of the left one
    if deduplicate_left_right_realisation(left_word, right_word):
        return

    # Replace the left word by it's liaison form (different form when the
    # word is in front of a vowel) when one of this cases is true.
    # - the left word is a singular masculing adjective
    # - the left word is a feminine singular possessive determiner
    # - the left word is a masculine singular non possessive determiner
    # if replace_word_by_liaison_form(right_word, right_word):
    #     return
