# encoding: utf-8

"""Test suite of the french morphology rules."""

import pytest

from nlglib.realisation.morphology.en import DeterminerAgrHelper


@pytest.fixture
def determiner_helper():
    return DeterminerAgrHelper()


class TestDeterminerHelper:

    @pytest.mark.parametrize('word', [
        'elephant',
        '8',
        '11',
        '18',
        '18000',
    ])
    def test_requires_an_true(self, determiner_helper, word):
        assert determiner_helper.requires_an(word)

    @pytest.mark.parametrize('word', [
        'cow',
        'hour',
        'one',
        '100',
        '180',
        '90',
    ])
    def test_requires_an_false(self, determiner_helper, word):
        assert not determiner_helper.requires_an(word)

    @pytest.mark.parametrize('text, np, expected', [
        ('I see a', 'elephant', 'I see an'),
        ('I see a', 'cow', 'I see a'),
        ('I see an', 'cow', 'I see a'),
    ])
    def test_ends_with_indefinite_article(self, determiner_helper, text, np, expected):
        actual = determiner_helper.check_ends_with_indefinite_article(text, np)
        assert actual == expected
