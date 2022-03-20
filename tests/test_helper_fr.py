# encoding: utf-8

"""Test suite of the French phrase syntax classes."""

import pytest
from unittest import mock

from nlglib.realisation.syntax.fr import FrenchNounPhraseHelper
from nlglib.spec.phrase import PhraseElement, AdjectivePhraseElement
from nlglib.spec.word import InflectedWordElement, WordElement
from nlglib.spec.string import StringElement
from nlglib.lexicon.lang import FRENCH
from nlglib.lexicon.feature.category import NOUN_PHRASE, ADJECTIVE
from nlglib.lexicon.feature.person import FIRST, SECOND, THIRD
from nlglib.lexicon.feature.gender import MASCULINE, FEMININE
from nlglib.lexicon.feature.number import SINGULAR, PLURAL


@pytest.fixture
def noun_helper_fr(lexicon_fr):
    return FrenchNounPhraseHelper()


@pytest.fixture
def phrase(lexicon_fr):
    return PhraseElement(category=NOUN_PHRASE, lexicon=lexicon_fr)


@pytest.mark.parametrize('person, number, gender, expected', [
    (FIRST, SINGULAR, MASCULINE, 'je'),
    (SECOND, SINGULAR, MASCULINE, 'tu'),
    (THIRD, SINGULAR, MASCULINE, 'il'),
    (THIRD, SINGULAR, FEMININE, 'elle'),
    (FIRST, PLURAL, MASCULINE, 'nous'),
    (SECOND, PLURAL, MASCULINE, 'vous'),
    (THIRD, PLURAL, MASCULINE, 'ils'),
    (THIRD, PLURAL, FEMININE, 'elles'),
])
def test_create_pronoun(noun_helper_fr, phrase, person, number, gender, expected):
    phrase.person = person
    phrase.number = number
    phrase.gender = gender
    pronoun = noun_helper_fr.create_pronoun(phrase)
    assert isinstance(pronoun, InflectedWordElement)
    assert pronoun.base_form == expected


@pytest.mark.parametrize('word, expected', [
    (None, False),
    (WordElement(base_form='premier'), False),
    (WordElement(base_form='second'), False),
    (WordElement(base_form='dernier'), False),
    (WordElement(base_form='deuxième'), True),
    (StringElement(string='premier', language=FRENCH), False),
    (StringElement(string='second', language=FRENCH), False),
    (StringElement(string='dernier', language=FRENCH), False),
    (StringElement(string='deuxième', language=FRENCH), True),
])
def test_is_ordinal(word, expected):
    assert FrenchNounPhraseHelper.is_ordinal(word) is expected


def test_add_null_modifier(lexicon_fr, noun_helper_fr, phrase):
    with mock.patch.object(PhraseElement, 'add_premodifier', autospec=True):
        with mock.patch.object(PhraseElement, 'add_postmodifier', autospec=True):
            noun_helper_fr.add_modifier(phrase, modifier=None)
            assert phrase.add_premodifier.call_count == 0
            assert phrase.add_postmodifier.call_count == 0


def test_add_postmodifier_word_element(lexicon_fr, noun_helper_fr, phrase):
    adj = lexicon_fr.first('meilleur', category=ADJECTIVE)
    noun_helper_fr.add_modifier(phrase, modifier=adj)
    assert not phrase.premodifiers
    assert isinstance(phrase.postmodifiers[0], WordElement)
    assert phrase.postmodifiers[0].base_form == 'meilleur'


def test_add_postmodifier_unknown_string_element(lexicon_fr, noun_helper_fr, phrase):
    assert 'badass' not in lexicon_fr
    noun_helper_fr.add_modifier(phrase, modifier='badass')
    assert 'badass' in lexicon_fr
    assert isinstance(phrase.postmodifiers[0], WordElement)
    assert not phrase.premodifiers
    assert phrase.postmodifiers[0].base_form == 'badass'


def test_add_postmodifier_unknown_complex_string_element(
        lexicon_fr, noun_helper_fr, phrase):
    assert 'totalement badass' not in lexicon_fr
    noun_helper_fr.add_modifier(phrase, modifier='totalement badass')
    assert 'totalement badass' not in lexicon_fr
    assert isinstance(phrase.postmodifiers[0], StringElement)
    assert not phrase.premodifiers
    assert phrase.postmodifiers[0].realisation == 'totalement badass'


def test_add_premodifier_ordinal_word(lexicon_fr, noun_helper_fr, phrase):
    adj = lexicon_fr.first('deuxième', category=ADJECTIVE)
    noun_helper_fr.add_modifier(phrase, modifier=adj)
    assert isinstance(phrase.premodifiers[0], WordElement)
    assert phrase.premodifiers[0].base_form == 'deuxième'
    assert not phrase.postmodifiers


def test_add_premodifier_inflected_word(lexicon_fr, noun_helper_fr, phrase):
    word = lexicon_fr.first('même')  # meme is preposed
    infl = word.inflex(number='plural')
    noun_helper_fr.add_modifier(phrase, modifier=infl)
    assert isinstance(phrase.premodifiers[0], InflectedWordElement)
    assert phrase.premodifiers[0] == infl
    assert not phrase.postmodifiers


@pytest.mark.parametrize('word', [
    'deuxième',  # ordinal
    'même'  # preposed
])
def test_add_premodifier_adjective_phrase(lexicon_fr, noun_helper_fr, phrase, word):
    adj_phrase = AdjectivePhraseElement(lexicon_fr)
    adj = lexicon_fr.first(word, category=ADJECTIVE)
    adj_phrase.head = adj
    noun_helper_fr.add_modifier(phrase, modifier=adj_phrase)
    assert phrase.premodifiers[0] == adj_phrase
    assert not phrase.postmodifiers
