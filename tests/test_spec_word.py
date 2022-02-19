# encoding: utf-8

"""Test suite of the WordElement class."""

import pytest

from nlglib.spec.word import WordElement, InflectedWordElement
from nlglib.lexicon.feature.category import NOUN, ADJECTIVE
from nlglib.lexicon.feature.number import PLURAL
from nlglib.lexicon.feature import NUMBER


@pytest.fixture(scope='module')
def word():
    return WordElement(
        base_form='fish',
        category=NOUN,
        id="E123",
        lexicon=None)


@pytest.mark.parametrize("word,other_word", [
    (
        WordElement('beau', ADJECTIVE, "E123", None),
        WordElement('beau', ADJECTIVE, "E123", None),
    )
])
def test_equality(word, other_word):
    assert word == other_word


@pytest.mark.parametrize("word,other_word", [
    (
        WordElement('joli', ADJECTIVE, "E1", None),
        WordElement('beau', ADJECTIVE, "E123", None),
    ),
    (
        WordElement('joli', ADJECTIVE, "E1", None),
        'something',
    )
])
def test_inequality(word, other_word):
    assert word != other_word


def test_default_inflection_variant(word):
    word.default_inflection_variant = 'fish'
    assert word.default_inflection_variant == 'fish'


def test_inflectional_variants(word):
    word.inflectional_variants = ['fish', 'fishes']
    assert word.inflectional_variants == ['fish', 'fishes']


def test_spelling_variants(word):
    word.spelling_variants = ['clé', 'clef']
    assert word.spelling_variants == ['clé', 'clef']


def test_default_spelling_variant(word):
    word.default_spelling_variant = 'clé'
    assert word.default_spelling_variant == 'clé'


def test_children(word):
    assert word.children == []


def test_inflex(word):
    iw = word.inflex(number=PLURAL)
    assert isinstance(iw, InflectedWordElement)
    assert iw.features[NUMBER] == PLURAL
