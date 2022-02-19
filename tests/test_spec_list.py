# encoding: utf-8

"""Test suite of the ListElement class."""

import pytest

from nlglib.spec.list import ListElement
from nlglib.spec.word import InflectedWordElement
from nlglib.lexicon.feature import NUMBER
from nlglib.lexicon.feature.number import PLURAL


@pytest.fixture
def empty_list_elt():
    return ListElement()


@pytest.fixture
def nonempty_list_elt(word):
    return ListElement(word)


@pytest.fixture
def word(lexicon_fr):
    return lexicon_fr.first('voiture')


def test_append(empty_list_elt, word):
    empty_list_elt.append(word)
    assert word.parent == empty_list_elt


def test_extend(empty_list_elt, word):
    empty_list_elt.extend([word])
    assert word.parent == empty_list_elt


def test_length(empty_list_elt, nonempty_list_elt):
    assert len(empty_list_elt) == 0
    assert len(nonempty_list_elt) == 1


def test_bool(empty_list_elt, nonempty_list_elt):
    assert not empty_list_elt
    assert nonempty_list_elt


def test_container(empty_list_elt, word):
    with pytest.raises(IndexError):
        empty_list_elt[0]
    empty_list_elt.append(word)
    assert word == empty_list_elt[0]
    del empty_list_elt[0]
    with pytest.raises(IndexError):
        empty_list_elt[0]


def test_children(empty_list_elt, nonempty_list_elt, word, lexicon_fr):
    assert empty_list_elt.children == []
    assert nonempty_list_elt.children == [word]
    assert word.parent == nonempty_list_elt
    new_word = lexicon_fr.first('camion')
    nonempty_list_elt.children = [word, new_word]
    assert word.parent == nonempty_list_elt
    assert new_word.parent == nonempty_list_elt


def test_head(empty_list_elt, nonempty_list_elt, word):
    assert empty_list_elt.head is None
    assert nonempty_list_elt.head == word


def test_realise_syntaxt(nonempty_list_elt, lexicon_fr, word):
    new_word = lexicon_fr.first('camion')
    nonempty_list_elt.append(new_word)
    realised_list = nonempty_list_elt.realise_syntax()
    assert len(realised_list) == len(nonempty_list_elt)
    assert not nonempty_list_elt[0].base_word
    assert realised_list[0].base_word
    assert realised_list[0].base_word.parent == realised_list
    assert realised_list[0].parent == realised_list


def test_realise_morphology(empty_list_elt, lexicon_fr):
    l = empty_list_elt
    w = lexicon_fr.first('voiture')
    infl = InflectedWordElement(w)
    infl.features[NUMBER] = PLURAL
    l.append(infl)
    realised_list = l.realise_morphology()
    assert len(realised_list) == len(l)
    assert realised_list[0].realisation == 'voitures'


@pytest.mark.incomplete
def test_realise_orthography():
    pass
