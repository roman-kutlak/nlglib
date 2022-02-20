
from nlglib.lexicon import feature
import nlglib.lexicon.feature.lexical
from nlglib.lexicon.feature import ELIDED, NUMBER, form, tense
from nlglib.lexicon.feature import category as cat
from nlglib.lexicon.feature import internal
from nlglib.lexicon.feature import clause
from nlglib.lexicon.feature import discourse
from nlglib.lexicon.feature import person
from nlglib.lexicon.feature import number
from nlglib.lexicon.feature import gender

from nlglib.spec.phrase import make_adjective_phrase, CoordinatedPhraseElement
from nlglib.spec.phrase import make_noun_phrase, make_verb_phrase

#
# lexicon = new
# XMLLexicon(); // built in lexicon
#
# this.phraseFactory = new
# NLGFactory(this.lexicon);
# this.realiser = new
# Realiser(this.lexicon);
#
# this.man = this.phraseFactory.createNounPhrase("the", "man"); // $NON - NLS - 1$ // $NON - NLS - 2$
# this.woman = this.phraseFactory.createNounPhrase("the", "woman"); // $NON - NLS - 1$ // $NON
# // -NLS - 2$
# this.dog = this.phraseFactory.createNounPhrase("the", "dog"); // $NON - NLS - 1$ // $NON - NLS - 2$
# this.boy = this.phraseFactory.createNounPhrase("the", "boy"); // $NON - NLS - 1$ // $NON - NLS - 2$
#
# this.beautiful = this.phraseFactory.createAdjectivePhrase("beautiful"); // $NON - NLS - 1$
# this.stunning = this.phraseFactory.createAdjectivePhrase("stunning"); // $NON - NLS - 1$
# this.salacious = this.phraseFactory.createAdjectivePhrase("salacious"); // $NON - NLS - 1$
#
# this.onTheRock = this.phraseFactory.createPrepositionPhrase("on"); // $NON - NLS - 1$
# this.np4 = this.phraseFactory.createNounPhrase("the", "rock"); // $NON - NLS - 1$ // $NON - NLS - 2$
# this.onTheRock.addComplement(this.np4);
#
# this.behindTheCurtain = this.phraseFactory.createPrepositionPhrase("behind"); // $NON - NLS - 1$
# this.np5 = this.phraseFactory.createNounPhrase("the", "curtain"); // $NON - NLS - 1$
# // $NON - NLS - 2$
# this.behindTheCurtain.addComplement(this.np5);
#
# this.inTheRoom = this.phraseFactory.createPrepositionPhrase("in"); // $NON - NLS - 1$
# this.np6 = this.phraseFactory.createNounPhrase("the", "room"); // $NON - NLS - 1$ // $NON - NLS - 2$
# this.inTheRoom.addComplement(this.np6);
#
# this.underTheTable = this.phraseFactory.createPrepositionPhrase("under"); // $NON - NLS - 1$
# this.underTheTable.addComplement(this.phraseFactory.createNounPhrase("the", "table"));
# // $NON - NLS - 1$ // $NON - NLS - 2$
#
# this.proTest1 = this.phraseFactory.createNounPhrase("the", "singer"); // $NON - NLS - 1$
# // $NON - NLS - 2$
# this.proTest2 = this.phraseFactory.createNounPhrase("some", "person"); // $NON - NLS - 1$
# // $NON - NLS - 2$
#
# this.kick = this.phraseFactory.createVerbPhrase("kick"); // $NON - NLS - 1$
# this.kiss = this.phraseFactory.createVerbPhrase("kiss"); // $NON - NLS - 1$
# this.walk = this.phraseFactory.createVerbPhrase("walk"); // $NON - NLS - 1$
# this.talk = this.phraseFactory.createVerbPhrase("talk"); // $NON - NLS - 1$
# this.getUp = this.phraseFactory.createVerbPhrase("get up"); // $NON - NLS - 1$
# this.fallDown = this.phraseFactory.createVerbPhrase("fall down"); // $NON - NLS - 1$
# this.give = this.phraseFactory.createVerbPhrase("give"); // $NON - NLS - 1$
# this.say = this.phraseFactory.createVerbPhrase("say"); // $NON - NLS - 1$
#
# def test_basic_example(lexicon_fr):
#     """Test from original github page."""
#     un = lexicon_fr.first('un', category=DETERMINER)
#     maison = lexicon_fr.first('maison', category=NOUN)
#     maison = maison.inflex(gender=FEMININE)
#     beau = lexicon_fr.first('beau', category=ADJECTIVE)
#     perdu = lexicon_fr.first('perdu', category=ADJECTIVE)
#     phrase = make_noun_phrase(lexicon=lexicon_fr, specifier=un, noun=maison, modifiers=[beau, perdu])
#     syntaxically_realised_phrase = phrase.realise()
#     # # FIXME: there is a bug which loses the features of the head noun
#     syntaxically_realised_phrase.gender = FEMININE
#     morphologically_realised_phrase = syntaxically_realised_phrase.realise_morphology()
#
#     expected = ['une', 'belle', 'maison', 'perdue']
#     actual = [x.realisation for x in morphologically_realised_phrase.components]
#     assert actual == expected


def check_and_return_realisation(element, expected):
    realisation = element.realise()
    actual = [x.realisation for x in realisation.components]
    assert actual == expected
    return realisation


def test_adjectives(lexicon_en):
    """AdjectivePhraseTest from simplenlg"""
    salacious = make_adjective_phrase(lexicon_en, 'salacious')
    salacious.add_pre_modifier("incredibly")
    
    realisation = salacious.realise()
    expected = ['incredibly', 'salacious']
    actual = [x.realisation for x in realisation.components]
    assert actual == expected
    
    beautiful = make_adjective_phrase(lexicon_en, 'beautiful')
    beautiful.add_pre_modifier("amazingly")
    
    expected = ['amazingly', 'beautiful']
    actual = [x.realisation for x in beautiful.realise().components]
    assert actual == expected

    cc = CoordinatedPhraseElement(salacious, beautiful, lexicon=lexicon_en)

    expected = ["incredibly", "salacious", "and", "amazingly", "beautiful"]
    realisation = cc.realise()
    adjp1, conj, adjp2 = realisation[0].children
    actual = [x.realisation for x in adjp1.children] + [conj.realisation] + [x.realisation for x in adjp2.children]
    assert actual == expected

    # // form the adjphrase "incredibly beautiful"
    # this.beautiful.addPreModifier("amazingly"); //$NON-NLS-1$
    # Assert.assertEquals("amazingly beautiful", this.realiser //$NON-NLS-1$
    #     .realise(this.beautiful).getRealisation());
    #
    # // coordinate the two aps
    # CoordinatedPhraseElement coordap = new CoordinatedPhraseElement(this.salacious,
    #     this.beautiful);
    # Assert.assertEquals("incredibly salacious and amazingly beautiful", //$NON-NLS-1$
    #     this.realiser.realise(coordap).getRealisation());
    #
    # // changing the inner conjunction
    # coordap.setFeature(Feature.CONJUNCTION, "or"); //$NON-NLS-1$
    # Assert.assertEquals("incredibly salacious or amazingly beautiful", //$NON-NLS-1$
    #     this.realiser.realise(coordap).getRealisation());
    #
    # // coordinate this with a new AdjPhraseSpec
    # CoordinatedPhraseElement coord2 = new CoordinatedPhraseElement(coordap, this.stunning);
    # Assert.assertEquals("incredibly salacious or amazingly beautiful and stunning", //$NON
    #     // -NLS-1$
    #     this.realiser.realise(coord2).getRealisation());
    #
    # // add a premodifier the coordinate phrase, yielding
    # // "seriously and undeniably incredibly salacious or amazingly beautiful
    # // and stunning"
    # CoordinatedPhraseElement preMod = new CoordinatedPhraseElement(
    #     new StringElement("seriously"),
    #     new StringElement("undeniably")); //$NON-NLS-1$//$NON-NLS-2$
    #
    # coord2.addPreModifier(preMod);
    # Assert.assertEquals("seriously and undeniably incredibly salacious or amazingly beautiful" +
    #         " and stunning", //$NON-NLS-1$
    #     this.realiser.realise(coord2).getRealisation());
    #
    # // adding a coordinate rather than coordinating should give a different
    # // result
    # coordap.addCoordinate(this.stunning);
    # Assert.assertEquals("incredibly salacious, amazingly beautiful or stunning", //$NON-NLS-1$
    #     this.realiser.realise(coordap).getRealisation());


def test_noun_phrase(lexicon_en):
    house = make_noun_phrase(lexicon_en, "the", "house")
    check_and_return_realisation(house, ["the", "house"])

    house.number = feature.number.PLURAL
    realisation = check_and_return_realisation(house, ["the", "house"])
    assert realisation.components[1].number == number.PLURAL

    house.add_modifier("small")
    check_and_return_realisation(house, ["the", "small", "house"])


def test_verb_phrase(lexicon_en):
    run = make_verb_phrase(lexicon_en, "run")
    check_and_return_realisation(run, ["run"])
