# encoding: utf-8

"""Test suite of the phrase classes"""


import pytest

from nlglib.spec.phrase import AdjectivePhraseElement, NounPhraseElement
from nlglib.lexicon.feature.category import ADJECTIVE, NOUN, DETERMINER
from nlglib.lexicon.feature.discourse import SPECIFIER


@pytest.fixture
def adj_phrase(lexicon_fr):
    return AdjectivePhraseElement(lexicon_fr)


@pytest.fixture
def noun_phrase(lexicon_fr):
    return NounPhraseElement(lexicon_fr)


def test_set_adjective(lexicon_fr, adj_phrase):
    adj = lexicon_fr.first('meilleur')
    adj_phrase.adjective = adj
    assert adj_phrase.adjective == adj


def test_set_str_adjective(lexicon_fr, adj_phrase):
    adj = lexicon_fr.first('meilleur')
    adj_phrase.adjective = 'meilleur'
    assert adj_phrase.adjective == adj


def test_set_unknown_str_adjective(lexicon_fr, adj_phrase):
    assert 'swag' not in lexicon_fr
    adj_phrase.adjective = 'swag'
    assert 'swag' in lexicon_fr
    swag = lexicon_fr.first('swag', category=ADJECTIVE)
    assert adj_phrase.adjective == swag


def test_adj_phrase_children(lexicon_fr, adj_phrase):
    adj = lexicon_fr.first('meilleur')
    adj_phrase.adjective = 'meilleur'
    assert adj_phrase.get_children() == [adj]


def test_noun_phrase_children(lexicon_fr, noun_phrase):
    un = lexicon_fr.first('un', category=DETERMINER)
    beau = lexicon_fr.first('beau', category=ADJECTIVE)
    endroit = lexicon_fr.first('endroit', category=NOUN)
    perdu = lexicon_fr.first('perdu', category=ADJECTIVE)
    noun_phrase.head = endroit
    noun_phrase.specifier = un
    noun_phrase.add_modifier(beau)  # 'beau' is preposed, as indicated in lexicon
    noun_phrase.add_modifier(perdu)
    assert noun_phrase.get_children() == [un, beau, endroit, perdu]
    assert noun_phrase.premodifiers == [beau]
    assert noun_phrase.postmodifiers == [perdu]
    assert un.parent == noun_phrase
    assert beau.parent == noun_phrase
    assert endroit.parent == noun_phrase
    assert perdu.parent == noun_phrase
    assert un.discourse_function == SPECIFIER
    assert beau.discourse_function is None  # should it be None?
    assert endroit.discourse_function is None  # should it be None?
    assert perdu.discourse_function is None  # should it be None?


def test_get_set_noun_phrase_noun(lexicon_fr, noun_phrase):
    noun = lexicon_fr.first('maison', category=NOUN)
    noun_phrase.noun = noun
    assert noun_phrase.head == noun
    assert noun_phrase.noun == noun


def test_get_set_noun_phrase_pronoun(lexicon_fr, noun_phrase):
    pronoun = lexicon_fr.first('celui-ci', category=NOUN)
    noun_phrase.pronoun = pronoun
    assert noun_phrase.head == pronoun
    assert noun_phrase.pronoun == pronoun
