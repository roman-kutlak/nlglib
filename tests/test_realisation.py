import logging

import pytest

from nlglib.spec.string import StringElement as String
from nlglib.spec.word import WordElement as Word, InflectedWordElement as Inflection
from nlglib.spec.phrase import Clause, NounPhraseElement, VerbPhraseElement
from nlglib.lexicon import feature as f
from nlglib.lexicon.feature import category
from nlglib.realisation.realiser.base import Realiser
from nlglib.language.en import English
from nlglib.realisation.syntax.en import SyntaxProcessor
from nlglib.realisation.morphology.en import MorphologyProcessor
from nlglib.realisation.ortography.en import OrtographyProcessor


@pytest.fixture
def en(lexicon_en):
    return English(
        lexicon=lexicon_en,
        syntax=SyntaxProcessor(),
        morphology=MorphologyProcessor(),
        ortography=OrtographyProcessor(),
    )


@pytest.fixture
def realiser(en):
    return Realiser(en)


class TestElementRealisation:

    def test_string(self, en, realiser):
        s = String('hello')
        expected = 'hello'
        actual = realiser(s)
        assert actual == expected

    def test_word(self, en, realiser):
        s = en.noun('house')
        expected = 'house'
        actual = realiser(s)
        assert actual == expected

    def test_word_with_feature(self, en, realiser):
        s = en.noun('house', number=f.number.PLURAL)
        expected = 'houses'
        actual = realiser(s)
        assert actual == expected

    def test_inflected_word(self, en, realiser):
        s = en.noun('house').inflex(number=f.number.PLURAL)
        expected = 'houses'
        actual = realiser(s)
        assert actual == expected


class TestAdjectivePhraseRealisation:

    def test_adjective_phrase_head(self, en, realiser):
        expected = 'happy'
        phrase = en.adjective_phrase("happy")
        actual = realiser(phrase)
        assert actual == expected

    def test_adjective_phrase_premodified(self, en, realiser):
        expected = 'very happy'
        phrase = en.adjective_phrase("happy")
        phrase.add_premodifier(en.adverb('very'))
        actual = realiser(phrase)
        assert actual == expected

    def test_adjective_phrase_postmodified(self, en, realiser):
        expected = 'happy enough'
        phrase = en.adjective_phrase("happy")
        phrase.add_postmodifier(en.adverb('enough'))
        actual = realiser(phrase)
        assert actual == expected

    def test_adjective_phrase_postmodified_by_phrase(self, en, realiser):
        expected = 'advanced for her age'
        phrase = en.adjective_phrase("advanced")
        phrase.add_postmodifier(en.preposition_phrase('for', en.noun_phrase("her", "age")))
        actual = realiser(phrase)
        assert actual == expected

    @pytest.mark.xfail(reason='verb phrases not tested yet and boviously missing something ther')
    def test_adjective_phrase_complemented_by_phrase(self, en, realiser):
        expected = 'willing to volunteer'
        phrase = en.adjective_phrase("willing")
        phrase.add_complement(en.verb_phrase('volunteer', form='infinitive'))
        actual = realiser(phrase)
        assert actual == expected

    def test_adjective_phrase_complemented_by_phrase_canned(self, en, realiser):
        expected = 'willing to volunteer'
        phrase = en.adjective_phrase("willing")
        phrase.add_complement(en.text('to volunteer'))
        actual = realiser(phrase)
        assert actual == expected


class TestAdverbPhraseRealisation:

    def test_adverb_phrase_head(self, en, realiser):
        expected = 'rarely'
        phrase = en.adverb_phrase("rarely")
        actual = realiser(phrase)
        assert actual == expected

    def test_adverb_phrase_premodified(self, en, realiser):
        expected = 'very quickly'
        phrase = en.adverb_phrase("quickly")
        phrase.add_premodifier(en.adverb('very'))
        actual = realiser(phrase)
        assert actual == expected

    def test_adverb_phrase_postmodified(self, en, realiser):
        expected = 'happily enough'
        phrase = en.adverb_phrase("happily")
        phrase.add_postmodifier(en.adverb('enough'))
        actual = realiser(phrase)
        assert actual == expected

    def test_adverb_phrase_complemented_by_phrase(self, en, realiser):
        expected = 'unfortunately for me'
        phrase = en.adverb_phrase("unfortunately")
        phrase.add_postmodifier(en.preposition_phrase('for', en.pronoun('me')))
        actual = realiser(phrase)
        assert actual == expected


class TestNounPhraseRealisation:

    def test_singular_np_definite(self, en, realiser):
        expected = 'the house'
        phrase = en.noun_phrase("the", "house")
        actual = realiser(phrase)
        assert actual == expected

    def test_plural_np_definite(self, en, realiser):
        expected = 'the houses'
        phrase = en.noun_phrase("the", "house", number=f.number.PLURAL)
        actual = realiser(phrase)
        assert actual == expected

    def test_singular_np_indefinite(self, en, realiser):
        expected = 'a house'
        phrase = en.noun_phrase("a", "house")
        actual = realiser(phrase)
        assert actual == expected

    @pytest.mark.xfail(reason="Logic current in determiner morphology but incorrectly called")
    def test_plural_np_indefinite(self, en, realiser):
        expected = 'some houses'
        phrase = en.noun_phrase("a", "house", number=f.number.PLURAL)
        actual = realiser(phrase)
        assert actual == expected


# class TestDocumentRealisation:
#
#     def test_singular_np(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         expected = 'the monkey'
#         monkey = NounPhraseElement(lexicon=lexicon_en)
#         monkey.noun = lexicon_en.first('monkey', category=category.NOUN)
#         monkey.specifier = lexicon_en.first('the', category=category.DETERMINER)
#         actual = realiser(monkey)
#         assert actual == expected
#


# class TestRealiser:
#
#     def test_simple(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         text = realiser(get_clause())
#         expected = 'You say hello.'
#         assert expected == text
#
#     def test_complex(self, lexicon_en):
#         c = get_clause()
#
#         realiser = Realiser(lexicon_en)
#         text = realiser.realise(c)
#         expected = 'You say hello.'
#         assert expected == text
#
#         c.features['Form'] = "IMPERATIVE"
#
#         text = realiser.realise(c)
#         expected = 'Say hello.'
#         # TODO: implement imperative in simple realisation?
#         # assert expected == text
#
#         text = realiser.realise(get_test_doc())
#         expected = Document(None, 'Hello.', 'You say hello.')
#         assert expected == text
#
#
# class TestStringRealisation:
#
#     def test_string(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         s = String('hello')
#         expected = 'hello'
#         actual = realiser(s)
#         assert actual == expected
#
#     def test_word(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         s = Word('house', 'NOUN')
#         expected = 'house'
#         actual = realiser(s)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         s = Word('house', 'NOUN', {'Number': 'PLURAL'})
#         expected = 'houses'
#         actual = realiser(s)
#         # TODO: implement pluralisation?
#         # assert actual == expected
#
#     def test_var(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         s = Var(0, 'truck1')
#         expected = 'truck1'
#         actual = realiser(s)
#         assert actual == expected
#
#     def test_coordination(self, lexicon_en):
#         w1 = Word('truck', 'NOUN')
#         w2 = Word('car', 'NOUN')
#         w3 = Word('motorbike', 'NOUN')
#
#         realiser = Realiser(lexicon_en)
#         expected = ''
#         s = Coordination()
#         actual = realiser(s)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         expected = 'truck'
#         s = Coordination(w1)
#         actual = realiser(s)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         expected = 'truck and car'
#         s = Coordination(w1, w2)
#         actual = realiser(s)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         expected = 'truck, car and motorbike'
#         s = Coordination(w1, w2, w3)
#         actual = realiser(s)
#         assert actual == expected
#
#     def test_clause(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = Clause(Word('Peter', 'NOUN'),
#                    Word('run', 'VERB'))
#         expected = 'Peter run'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = Clause(Word('Peter', 'NOUN'),
#                    Word('run', 'VERB'),
#                    front_modifiers=[String('yesterday')])
#         expected = 'yesterday Peter run'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = Clause(Word('Peter', 'NOUN'),
#                    Word('run', 'VERB'),
#                    front_modifiers=[String('yesterday')],
#                    postmodifiers=[String('abundantly')])
#         expected = 'yesterday Peter run abundantly'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = Clause(Word('Peter', 'NOUN'),
#                    Word('run', 'VERB'),
#                    front_modifiers=['yesterday'],
#                    postmodifiers=['abundantly'])
#         expected = 'yesterday Peter run abundantly'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_np(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = NounPhrase(Word('house', 'NOUN'),
#                        Word('this', 'DETERMINER'))
#         expected = 'this house'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = NounPhrase(Word('house', 'NOUN'),
#                        Word('this', 'DETERMINER'),
#                        premodifiers=['tall', 'yellow'],
#                        postmodifiers=['that we lived in'])
#         expected = 'this tall yellow house that we lived in'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_vp(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = VerbPhrase(Word('hit', 'VERB'),
#                        String('the ball'),
#                        String('with the bat'))
#         expected = 'hit the ball with the bat'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = VerbPhrase(Word('hit', 'VERB'),
#                        NounPhrase(Word('ball', 'NOUN'), 'the'),
#                        String('with the bat'))
#         expected = 'hit the ball with the bat'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_pp(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = PrepositionPhrase(Word('in', 'PREPOSITION'),
#                               String('the house'))
#         expected = 'in the house'
#         actual = realiser(c)
#         assert actual == expected
#
#         realiser = Realiser(lexicon_en)
#         c = PrepositionPhrase(Word('in', 'PREPOSITION'),
#                               NounPhrase(Word('house', 'NOUN'), Word('the', 'DETERMINER')))
#         expected = 'in the house'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_adjp(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = AdjectivePhrase(Word('green', 'ADJECTIVE'))
#         expected = 'green'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_advp(self, lexicon_en):
#         realiser = Realiser(lexicon_en)
#         c = AdverbPhrase(Word('rarely', 'ADVERB'))
#         expected = 'rarely'
#         actual = realiser(c)
#         assert actual == expected
#
#     def test_complex(self, lexicon_en):
#         house = NounPhrase('house', 'the')
#         shopping = NounPhrase('shopping', 'the')
#         put = VerbPhrase('put', shopping, PrepositionPhrase('in', house))
#         s = Clause(NounPhrase('Peter'), put)
#         expected = 'Peter put the shopping in the house'
#         realiser = Realiser(lexicon_en)
#         actual = realiser(s)
#         assert actual == expected


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
