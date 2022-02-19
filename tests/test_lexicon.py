# encoding: utf-8

"""Test suite of the lexicon package"""


import pytest

# noinspection PyPep8Naming
from xml.etree import cElementTree as ET

from nlglib.lexicon.fr import FrenchLexicon
from nlglib.lexicon.en import EnglishLexicon
from nlglib.lexicon.feature.internal import DISCOURSE_FUNCTION
from nlglib.lexicon.feature.discourse import SUBJECT
from nlglib.lexicon.feature.lexical.fr import VOWEL_ELISION
from nlglib.lexicon.feature.number import SINGULAR
from nlglib.lexicon.feature.person import FIRST
from nlglib.lexicon.feature import PERSON, NUMBER
from nlglib.lexicon.feature.category import (NOUN, VERB, ANY, DETERMINER, ADJECTIVE, ADVERB, PRONOUN)
from nlglib.lexicon.feature.lexical import (COMPARATIVE, SUPERLATIVE, PREDICATIVE, QUALITATIVE)
from nlglib.spec.word import WordElement


def _list(x):
    if not x:
        return []
    return [x] if not isinstance(x, list) else x


def test_lexicon_supported_languages():
    assert FrenchLexicon(auto_index=False).lexicon_filepath
    assert EnglishLexicon(auto_index=False).lexicon_filepath


@pytest.fixture
def word_node():
    """Return an XML tree representing a word node."""
    word_node = ET.Element('word')
    ET.SubElement(word_node, 'base').text = 'être'
    ET.SubElement(word_node, 'category').text = 'verb'
    ET.SubElement(word_node, 'id').text = 'E0012152'
    ET.SubElement(word_node, 'present1s').text = 'suis'
    ET.SubElement(word_node, 'present2s').text = 'es'
    ET.SubElement(word_node, 'present3s').text = 'est'
    ET.SubElement(word_node, 'present1p').text = 'sommes'
    ET.SubElement(word_node, 'present2p').text = 'êtes'
    ET.SubElement(word_node, 'present3p').text = 'sont'
    ET.SubElement(word_node, 'imperative2s').text = 'sois'
    ET.SubElement(word_node, 'imperative1p').text = 'soyons'
    ET.SubElement(word_node, 'imperative2p').text = 'soyez'
    ET.SubElement(word_node, 'future_radical').text = 'ser'
    ET.SubElement(word_node, 'imparfait_radical').text = 'êt'
    ET.SubElement(word_node, 'pastParticiple').text = 'été'
    ET.SubElement(word_node, 'presentParticiple').text = 'étant'
    ET.SubElement(word_node, 'subjunctive1s').text = 'sois'
    ET.SubElement(word_node, 'subjunctive2s').text = 'sois'
    ET.SubElement(word_node, 'subjunctive3s').text = 'soit'
    ET.SubElement(word_node, 'subjunctive1p').text = 'soyons'
    ET.SubElement(word_node, 'subjunctive2p').text = 'soyez'
    ET.SubElement(word_node, 'subjunctive3p').text = 'soient'
    ET.SubElement(word_node, 'copular')
    return word_node


def test_indexed(empty_lexicon_fr, lexicon_fr):
    assert not empty_lexicon_fr.indexed
    assert lexicon_fr.indexed


def test_word_from_node(empty_lexicon_fr, word_node):
    word_elt = empty_lexicon_fr.word_from_node(word_node)
    assert isinstance(word_elt, WordElement)
    assert word_elt.id == 'E0012152'
    assert word_elt.base_form == 'être'
    assert word_elt.category == 'VERB'
    assert word_elt['present1s'] == 'suis'
    assert word_elt['present2s'] == 'es'
    assert word_elt['copular'] is True
    assert word_elt.default_inflection_variant == 'reg'
    assert word_elt.inflection_variants == ['reg']


def test_index_word(empty_lexicon_fr, word_node):
    lex = empty_lexicon_fr
    word_elt = lex.word_from_node(word_node)
    assert not lex.words
    assert not lex.id_index
    assert not lex.base_index
    assert not lex.variant_index
    assert not lex.category_index
    lex.index_word(word_elt)
    assert lex.id_index['E0012152'] == word_elt
    assert lex.base_index['être'] == [word_elt]
    assert lex.variant_index['être'] == [word_elt]
    assert lex.category_index['VERB'] == [word_elt]


def test_index_lexicon(lexicon_fr):
    assert lexicon_fr.words
    assert lexicon_fr.id_index
    assert lexicon_fr.base_index
    assert lexicon_fr.variant_index
    assert lexicon_fr.category_index


@pytest.mark.parametrize("word_base_form, category, expected", [
    ('son', ANY, 2),
    ('son', NOUN, 1),
    ('son', DETERMINER, 1),
    ('son', VERB, 0),
])
def test_lookup(lexicon_fr, word_base_form, category, expected):
    assert len(
        _list(lexicon_fr.get(word_base_form, category=category))) == expected


def test_lookup_null_return(lexicon_fr):
    assert lexicon_fr.get('BLAH', create_if_missing=False) is None


@pytest.mark.parametrize("word_base_form, auto_create, expected", [
    ('son', True, 2),
    ('son', False, 2),
    ('GRUB', False, 0),  # will not automatically be created
    ('GRUB', True, 1),  # will automatically be created
])
def test_getitem(lexicon_fr, word_base_form, auto_create, expected):
    matches = lexicon_fr.get(word_base_form, create_if_missing=auto_create)
    assert len(_list(matches)) == expected


@pytest.mark.incomplete('The variant index is not yet complete!')
def test_contains(lexicon_fr):
    assert 'son' in lexicon_fr
    assert 'vache_1' in lexicon_fr
    # assert SOME_VARIANT in lexicon_fr
    assert 'BLAHBLAH' not in lexicon_fr
    # check that last call did not have any side effect
    assert 'BLAHBLAH' not in lexicon_fr


@pytest.mark.parametrize("word_feature, expected_base_form", [
    ('manger', 'manger'),
    ('vache_1', 'vache'),
])
def test_get(lexicon_fr, word_feature, expected_base_form):
    assert lexicon_fr.get(word_feature)[0].base_form == expected_base_form


def test_first(lexicon_fr):
    son_categories = [w.category for w in lexicon_fr['son']]
    assert son_categories == [DETERMINER, NOUN]
    assert lexicon_fr.first('son', category=ANY).category == DETERMINER


def test_features1(lexicon_en):
    good = lexicon_en.first('good', category=ADJECTIVE)
    assert good[COMPARATIVE] == 'better'
    assert good[SUPERLATIVE] == 'best'
    assert good[PREDICATIVE] is True
    assert good[QUALITATIVE] is True


def test_getattr(lexicon_en):
    good = lexicon_en.first('good', category=ADJECTIVE)
    assert good.predicative is True
    assert good.superlative == 'best'
    assert good.comparative == 'better'
    assert good.qualitative is True


def test_features2(lexicon_en):
    woman = lexicon_en.first('woman', category=NOUN)
    assert woman.plural == 'women'
    assert woman.acronym_of is None
    assert not woman.proper
    assert 'uncount' not in woman.inflections


def test_features3(lexicon_en):
    sand = lexicon_en.first('sand', category=NOUN)
    assert 'nonCount' in sand.inflections
    assert sand.default_infl == 'nonCount'


def test_features4(lexicon_en):
    quickly = lexicon_en.first('E0051632')
    assert quickly.base_form == 'quickly'
    assert quickly.category == ADVERB
    assert quickly.verb_modifier
    assert not quickly.sentence_modifier
    assert not quickly.intensifier


def test_independant_words(lexicon_fr):
    le1 = lexicon_fr.first('le')
    le2 = lexicon_fr.first('le')
    assert le1 is not le2
    le1.realisation = "l'"
    assert le2.realisation == 'le'


@pytest.mark.parametrize('d1, d2, expected', [
    ({}, {}, True),
    ({'k1': 'v1', 'k2': 'v2'}, {'k1': 'v1', 'k2': 'v2'}, True),
    ({'k1': 'v1', 'k2': 'v2'}, {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}, True),
    ({'k1': 'v1', 'k2': 'v2'}, {'k1': 'v1'}, False),
    ({'k1': 'v1', 'k2': 'v2'}, {'k3': 'v3'}, False),
])
def test_is_dict_subset(d1, d2, expected):
    assert FrenchLexicon.is_dict_subset(d1, d2) is expected


def test_find_by_features(lexicon_fr):
    features = {
        PERSON: FIRST,
        NUMBER: SINGULAR,
        VOWEL_ELISION: True,
        DISCOURSE_FUNCTION: SUBJECT
    }
    word = lexicon_fr.find_by_features(features, category=PRONOUN)
    assert word.base_form == 'je'
