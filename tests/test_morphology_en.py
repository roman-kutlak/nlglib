# encoding: utf-8

"""Test suite of the french morphology rules."""

import pytest

from nlglib.lexicon.feature import NUMBER, IS_COMPARATIVE, IS_SUPERLATIVE, POSSESSIVE, TENSE, FORM, NEGATED, form
from nlglib.lexicon.feature import PERSON
from nlglib.lexicon.feature.category import ADVERB, NOUN, PRONOUN, VERB
from nlglib.lexicon.feature.gender import MASCULINE
from nlglib.lexicon.feature.lexical import REFLEXIVE, GENDER
from nlglib.lexicon.feature.number import PLURAL, SINGULAR
from nlglib.lexicon.feature.person import FIRST, SECOND, THIRD
from nlglib.lexicon.feature.tense import PRESENT, PAST
from nlglib.realisation.morphology.en import EnglishMorphologyRules


@pytest.fixture
def morph_rules_en():
    return EnglishMorphologyRules()


@pytest.mark.parametrize('word, expected', [
    ('aquarium', 'aquaria'),
    ('analysis', 'analyses'),
    ('book', 'books'),
    ('child', 'children'),
    ('person', 'people'),
    ('sheep', 'sheep'),
])
def test_pluralize(lexicon_en, morph_rules_en, word, expected):
    element = lexicon_en.first(word)
    element.features[NUMBER] = PLURAL
    assert morph_rules_en.morph_noun(element).realisation == expected


@pytest.mark.parametrize('determiner, features, expected', [
    ('a', {}, 'a'),
    ('a', {NUMBER: PLURAL}, 'some'),
    ('an', {}, 'an'),
    ('an', {NUMBER: PLURAL}, 'some'),
    ('the', {}, 'the'),
    ('that', {NUMBER: SINGULAR}, 'that'),
    ('that', {NUMBER: PLURAL}, 'those'),
    ('this', {NUMBER: SINGULAR}, 'this'),
    ('this', {NUMBER: PLURAL}, 'these'),
    ('these', {NUMBER: SINGULAR}, 'this'),
    ('those', {NUMBER: SINGULAR}, 'that'),
])
def test_morph_determiner(lexicon_en, morph_rules_en, determiner, features, expected):
    element = lexicon_en.first(determiner)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_en.morph_determiner(element)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, features, expected', [
    ('good', {}, 'good'),
    ('good', {IS_COMPARATIVE: True}, 'better'),
    ('good', {IS_SUPERLATIVE: True}, 'best'),
    ('sad', {}, 'sad'),
    ('sad', {IS_COMPARATIVE: True}, 'sadder'),
    ('sad', {IS_SUPERLATIVE: True}, 'saddest'),
    ('brainy', {}, 'brainy'),
    ('brainy', {IS_COMPARATIVE: True}, 'brainier'),
    ('brainy', {IS_SUPERLATIVE: True}, 'brainiest'),
    ('gray', {}, 'gray'),
    ('gray', {IS_COMPARATIVE: True}, 'grayer'),
    ('gray', {IS_SUPERLATIVE: True}, 'grayest'),
    ('densely-populated', {}, 'densely-populated'),
    ('densely-populated', {IS_COMPARATIVE: True}, 'more densely-populated'),
    ('densely-populated', {IS_SUPERLATIVE: True}, 'most densely-populated'),
    ('fine', {}, 'fine'),
    ('fine', {IS_COMPARATIVE: True}, 'finer'),
    ('fine', {IS_SUPERLATIVE: True}, 'finest'),
    ('fat', {}, 'fat'),
    ('fat', {IS_COMPARATIVE: True}, 'fatter'),
    ('fat', {IS_SUPERLATIVE: True}, 'fattest'),
    ('clear', {}, 'clear'),
    ('clear', {IS_COMPARATIVE: True}, 'clearer'),
    ('clear', {IS_SUPERLATIVE: True}, 'clearest'),
    ('personal', {}, 'personal'),
    ('personal', {IS_COMPARATIVE: True}, 'more personal'),
    ('personal', {IS_SUPERLATIVE: True}, 'most personal'),
    ('apt', {}, 'apt'),
    ('apt', {IS_COMPARATIVE: True}, 'more apt'),
    ('apt', {IS_SUPERLATIVE: True}, 'most apt'),
    ('tangled', {}, 'tangled'),
    ('tangled', {IS_COMPARATIVE: True}, 'more tangled'),
    ('tangled', {IS_SUPERLATIVE: True}, 'most tangled'),
])
def test_morph_adjective(lexicon_en, morph_rules_en, word, features, expected):
    element = lexicon_en.first(word)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_en.morph_adjective(element)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, features, expected', [
    ('quietly', {}, 'quietly'),
    ('quietly', {IS_COMPARATIVE: True}, 'more quietly'),
    ('quietly', {IS_SUPERLATIVE: True}, 'most quietly'),
    ('slowly', {}, 'slowly'),
    ('slowly', {IS_COMPARATIVE: True}, 'more slowly'),
    ('slowly', {IS_SUPERLATIVE: True}, 'most slowly'),
    ('seriously', {}, 'seriously'),
    ('seriously', {IS_COMPARATIVE: True}, 'more seriously'),
    ('seriously', {IS_SUPERLATIVE: True}, 'most seriously'),
    ('hard', {}, 'hard'),
    ('hard', {IS_COMPARATIVE: True}, 'harder'),
    ('hard', {IS_SUPERLATIVE: True}, 'hardest'),
    ('fast', {}, 'fast'),
    ('fast', {IS_COMPARATIVE: True}, 'faster'),
    ('fast', {IS_SUPERLATIVE: True}, 'fastest'),
    ('late', {}, 'late'),
    ('late', {IS_COMPARATIVE: True}, 'later'),
    ('late', {IS_SUPERLATIVE: True}, 'latest'),
    ('badly', {}, 'badly'),
    ('badly', {IS_COMPARATIVE: True}, 'worse'),
    ('badly', {IS_SUPERLATIVE: True}, 'worst'),
    ('far', {}, 'far'),
    ('far', {IS_COMPARATIVE: True}, 'farther'),
    ('far', {IS_SUPERLATIVE: True}, 'farthest'),
    ('early', {}, 'early'),
    ('early', {IS_COMPARATIVE: True}, 'earlier'),
    ('early', {IS_SUPERLATIVE: True}, 'earliest'),
    ('little', {}, 'little'),
    ('little', {IS_COMPARATIVE: True}, 'less'),
    ('little', {IS_SUPERLATIVE: True}, 'least'),
    ('well', {}, 'well'),
    ('well', {IS_COMPARATIVE: True}, 'better'),
    ('well', {IS_SUPERLATIVE: True}, 'best'),
])
def test_morph_adverb(lexicon_en, morph_rules_en, word, features, expected):
    element = lexicon_en.first(word, category=ADVERB)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_en.morph_adverb(element)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, features, expected', [
    # No transformation
    ('book', {}, 'book'),
    # Simple pluralisation based on plural feature of base word
    ('book', {NUMBER: PLURAL}, 'books'),
    # Pluralisation based on plural feature of base word
    ('analysis', {NUMBER: PLURAL}, 'analyses'),
    # Simple pluralisation using +s rule, because word is not in lexicon
    ('keyboard', {NUMBER: PLURAL}, 'keyboards'),
    # Possessive
    ('John', {POSSESSIVE: True}, "John's")
])
def test_morph_noun(lexicon_en, morph_rules_en, word, features, expected):
    base_word = lexicon_en.first(word)
    element = base_word.inflex(category=NOUN, **features)
    inflected_form = morph_rules_en.morph_noun(element, base_word)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, features, expected', [
    # No transformation
    ('I', {}, 'I'),
    ('I', {NUMBER: PLURAL, PERSON: FIRST}, 'we'),
    ('I', {NUMBER: PLURAL, PERSON: FIRST, REFLEXIVE: True}, 'ourselves'),
    ('I', {NUMBER: SINGULAR, PERSON: THIRD, POSSESSIVE: True, GENDER: MASCULINE}, 'his'),
])
def test_morph_pronoun(lexicon_en, morph_rules_en, word, features, expected):
    element = lexicon_en.first(word, PRONOUN)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_en.morph_pronoun(element)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, features, expected', [
    # No transformation
    ('be', {FORM: form.BARE_INFINITIVE}, 'be'),
    ('be', {NUMBER: SINGULAR, PERSON: FIRST}, 'am'),
    ('be', {NUMBER: SINGULAR, PERSON: SECOND}, 'are'),
    ('be', {NUMBER: SINGULAR, PERSON: THIRD}, 'is'),
    ('be', {NUMBER: PLURAL, PERSON: FIRST}, 'are'),
    ('be', {NUMBER: PLURAL, PERSON: SECOND}, 'are'),
    ('be', {NUMBER: PLURAL, PERSON: THIRD}, 'are'),
    ('be', {TENSE: PAST, NUMBER: SINGULAR, PERSON: FIRST}, 'was'),
    ('be', {TENSE: PAST, NUMBER: SINGULAR, PERSON: SECOND}, 'were'),
    ('be', {TENSE: PAST, NUMBER: SINGULAR, PERSON: THIRD}, 'was'),
    ('be', {TENSE: PAST, NUMBER: PLURAL, PERSON: FIRST}, 'were'),
    ('be', {TENSE: PAST, NUMBER: PLURAL, PERSON: SECOND}, 'were'),
    ('be', {TENSE: PAST, NUMBER: PLURAL, PERSON: THIRD}, 'were'),
    ('walk', {NEGATED: True}, 'walk'),
    ('walk', {PERSON: THIRD}, 'walks'),
    ('walk', {NUMBER: PLURAL, PERSON: THIRD}, 'walk'),
    ('walk', {TENSE: PRESENT, NUMBER: PLURAL, PERSON: THIRD}, 'walk'),
    ('walk', {TENSE: PAST}, 'walked'),
    ('walk', {FORM: form.IMPERATIVE}, 'walk'),
    ('walk', {FORM: form.PRESENT_PARTICIPLE}, 'walking'),
    ('walk', {FORM: form.PAST_PARTICIPLE}, 'walked'),
])
def test_morph_verb(lexicon_en, morph_rules_en, word, features, expected):
    base_word = lexicon_en.first(word, VERB)
    element = base_word.inflex(category=VERB, **features)
    inflected_form = morph_rules_en.morph_verb(element, base_word)
    assert inflected_form.realisation == expected
