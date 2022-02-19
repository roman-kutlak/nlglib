from nlglib.lexicon.feature.category import NOUN, ADJECTIVE, DETERMINER
from nlglib.spec.phrase import make_noun_phrase


def test_basic_example(lexicon_en):
    the = lexicon_en.first('the', category=DETERMINER)
    house = lexicon_en.first('house', category=NOUN)
    pretty = lexicon_en.first('pretty', category=ADJECTIVE)
    cozy = lexicon_en.first('cozy', category=ADJECTIVE)
    phrase = make_noun_phrase(lexicon=lexicon_en, specifier=the, noun=house, modifiers=[pretty, cozy])
    phrase.number = 'plural'
    syntaxically_realised_phrase = phrase.realise()
    morphologically_realised_phrase = syntaxically_realised_phrase.realise_morphology()
    expected = ['the', 'pretty', 'cozy', 'houses']
    actual = [x.realisation for x in morphologically_realised_phrase.components]
    assert actual == expected
