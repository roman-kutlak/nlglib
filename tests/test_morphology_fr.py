# encoding: utf-8

"""Test suite of the french morphology rules."""

import pytest

from nlglib.realisation.morphology.fr import FrenchMorphologyRules
from nlglib.spec.phrase import PhraseElement
from nlglib.spec.string import StringElement
from nlglib.lexicon.feature.category import ADJECTIVE, VERB_PHRASE, NOUN_PHRASE, VERB
from nlglib.lexicon.feature.lexical import GENDER
from nlglib.lexicon.feature import NUMBER, IS_COMPARATIVE
from nlglib.lexicon.feature.gender import MASCULINE, FEMININE
from nlglib.lexicon.feature.number import PLURAL, SINGULAR, BOTH
from nlglib.lexicon.feature.discourse import OBJECT, PRE_MODIFIER, FRONT_MODIFIER, POST_MODIFIER
from nlglib.lexicon.feature.internal import DISCOURSE_FUNCTION, COMPLEMENTS
from nlglib.lexicon.feature.person import FIRST, SECOND, THIRD
from nlglib.lexicon.feature.tense import PRESENT, PAST, FUTURE, CONDITIONAL
from nlglib.lexicon.feature.form import (
    BARE_INFINITIVE, SUBJUNCTIVE, GERUND, INFINITIVE,
    PRESENT_PARTICIPLE, PAST_PARTICIPLE, INDICATIVE, IMPERATIVE)
from nlglib.lexicon.feature import PERSON, TENSE, FORM


@pytest.fixture
def morph_rules_fr():
    return FrenchMorphologyRules()


@pytest.mark.parametrize('s, expected', [
    ('actuel', 'actuelle'),
    ('vieil', 'vieille'),
    ('bas', 'basse'),
    ('musicien', 'musicienne'),
    ('mignon', 'mignonne'),
    ('violet', 'violette'),
    ('affectueux', 'affectueuse'),
    ('premier', 'première'),
    ('amer', 'amère'),
    ('beau', 'belle'),
    ('gros', 'grosse'),
    ('aigu', 'aiguë'),
    ('long', 'longue'),
    ('migrateur', 'migratrice'),
    ('actif', 'active'),
    ('affairé', 'affairée'),
    ('abondant', 'abondante'),
])
def test_feminize(lexicon_fr, morph_rules_fr, s, expected):
    word = lexicon_fr.first(s, category=ADJECTIVE)
    word.feminine_singular = ''  # make sure all static rules are tested
    feminine_form = morph_rules_fr.feminize_singular_element(
        word, word.realisation)
    assert feminine_form == expected


@pytest.mark.parametrize('s, expected', [
    ('bas', 'bas'),
    ('vieux', 'vieux'),
    ('nez', 'nez'),
    ('tuyau', 'tuyaux'),
    ('cheveu', 'cheveux'),
    ('cheval', 'chevaux'),
    ('main', 'mains'),
])
def test_pluralize(morph_rules_fr, s, expected):
    assert morph_rules_fr.pluralize(s) == expected


@pytest.mark.parametrize('word, features, expected', [
    ('ce', {GENDER: MASCULINE}, 'ce'),
    ('ce', {GENDER: FEMININE}, 'cette'),
    ('ce', {GENDER: MASCULINE, NUMBER: PLURAL}, 'ces'),
    ('tout', {GENDER: MASCULINE}, 'tout'),
    ('tout', {GENDER: FEMININE}, 'toute'),
    ('tout', {GENDER: MASCULINE, NUMBER: PLURAL}, 'tous les'),
    ('tout', {GENDER: FEMININE, NUMBER: PLURAL}, 'toutes les'),
    ('ce -ci', {GENDER: MASCULINE}, 'ce'),
    ('ce -ci', {GENDER: FEMININE}, 'cette'),
    ('ce -ci', {GENDER: MASCULINE, NUMBER: PLURAL}, 'ces'),
])
def test_morph_determiner(lexicon_fr, morph_rules_fr, word, features, expected):
    element = lexicon_fr.first(word)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_fr.morph_determiner(element)
    assert inflected_form.realisation == expected


@pytest.mark.incomplete(
    'The whole part about parent and lineage has NOT been tested '
    'The tester needs to build a PhraseElement, with some parentage, '
    'and then morph an adjective in the PhraseElement.')
@pytest.mark.parametrize('word, features, expected', [
    ('bon', {IS_COMPARATIVE: True}, 'meilleur'),
    ('bon', {IS_COMPARATIVE: True, GENDER: FEMININE}, 'meilleure'),
    ('bon', {IS_COMPARATIVE: True, GENDER: FEMININE, NUMBER: PLURAL},
     'meilleures'),
])
def test_morph_adjective(lexicon_fr, morph_rules_fr, word, features, expected):
    element = lexicon_fr.first(word)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_fr.morph_adjective(element)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, base_word, features, expected', [
    # No transformation
    ('voiture', 'voiture', {}, 'voiture'),
    # Simple pluralisation based on plural feature of base word
    ('voiture', 'voiture', {NUMBER: PLURAL}, 'voitures'),
    # PLuralisation based on plural feature of base word
    ('oeil', 'oeil', {NUMBER: PLURAL}, 'yeux'),
    # No idea what I'm doing
    ('gars', 'fille', {GENDER: MASCULINE}, 'garçon'),
    # Simple pluralisation using +s rule, because word is not
    # in lexicon
    ('clavier', 'clavier', {NUMBER: PLURAL}, 'claviers'),
    ('directeur', 'directeur', {NUMBER: PLURAL, GENDER: FEMININE}, 'directrices'),
])
def test_morph_noun(lexicon_fr, morph_rules_fr, word, base_word, features, expected):
    base_word = lexicon_fr.first(base_word)
    element = lexicon_fr.first(word)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_fr.morph_noun(element, base_word)
    assert inflected_form.realisation == expected


@pytest.mark.parametrize('word, base_word, features, expected', [
    ('bientôt', 'bientôt', {}, 'bientôt'),
    ('bien', 'bien', {IS_COMPARATIVE: True}, 'mieux'),
    # bientôt does not compare
    ('bientôt', 'bientôt', {IS_COMPARATIVE: True}, 'bientôt'),
])
def test_morph_adverb(lexicon_fr, morph_rules_fr, word, base_word, features, expected):
    base_word = lexicon_fr.first(base_word)
    element = lexicon_fr.first(word)
    for k, v in features.items():
        element.features[k] = v
    inflected_form = morph_rules_fr.morph_adverb(element, base_word)
    assert inflected_form.realisation == expected


def test_get_verb_parent(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('avoir')
    parent, agreement = morph_rules_fr.get_verb_parent(verb)
    assert parent is None
    assert agreement is False


def test_get_verb_parent2(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('avoir')
    p = PhraseElement(lexicon=lexicon_fr, category=VERB_PHRASE)
    verb.parent = p
    parent, agreement = morph_rules_fr.get_verb_parent(verb)
    assert parent == p
    assert agreement is True


def test_get_verb_parent3(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('avoir')
    p = PhraseElement(lexicon=lexicon_fr, category=VERB_PHRASE)
    verb.parent = p
    gp = PhraseElement(lexicon=lexicon_fr, category=VERB_PHRASE)
    gp.gender = FEMININE
    parent, agreement = morph_rules_fr.get_verb_parent(verb)
    assert parent == gp
    assert agreement is True


@pytest.mark.parametrize('mod_func', [FRONT_MODIFIER, PRE_MODIFIER, POST_MODIFIER])
def test_get_verb_parent4(lexicon_fr, morph_rules_fr, mod_func):
    verb = lexicon_fr.first('avoir')
    verb.features[DISCOURSE_FUNCTION] = mod_func
    p = PhraseElement(lexicon=lexicon_fr, category=NOUN_PHRASE)
    verb.parent = p
    parent, agreement = morph_rules_fr.get_verb_parent(verb)
    assert parent == p
    assert agreement is True


@pytest.mark.parametrize('mod_func', [FRONT_MODIFIER, PRE_MODIFIER, POST_MODIFIER])
def test_get_verb_parent5(lexicon_fr, morph_rules_fr, mod_func):
    verb = lexicon_fr.first('avoir')
    verb.features[DISCOURSE_FUNCTION] = mod_func
    p = PhraseElement(lexicon=lexicon_fr, category=NOUN_PHRASE)
    w = lexicon_fr.first('cheval')
    w.features[DISCOURSE_FUNCTION] = OBJECT
    p.features[COMPLEMENTS] = [w]
    verb.parent = p
    parent, agreement = morph_rules_fr.get_verb_parent(verb)
    assert parent == w
    assert agreement is True


@pytest.mark.parametrize('verb, radical, number, group', [
    ('aimer', 'aim', SINGULAR, 1),
    ('aimer', 'aim', PLURAL, 1),
    ('choir', 'choi', SINGULAR, 2),
    ('choir', 'choy', PLURAL, 2),
    ('finir', 'fini', SINGULAR, 2),
    ('finir', 'finiss', PLURAL, 2),
    ('haïr', 'hai', SINGULAR, 2),
    ('haïr', 'haïss', PLURAL, 2),
    ('vendre', 'vend', SINGULAR, 3),
    ('vendre', 'vend', PLURAL, 3),
    ('mettre', 'met', SINGULAR, 3),
    ('mettre', 'mett', PLURAL, 3),
])
def test_get_present_radical(morph_rules_fr, verb, radical, number, group):
    verb_tuple = morph_rules_fr.get_present_radical(verb, number)
    assert verb_tuple.radical == radical
    assert verb_tuple.group == group


def test_get_present_radical_unrecognized_verb(morph_rules_fr):
    with pytest.raises(ValueError):
        morph_rules_fr.get_present_radical('plop', SINGULAR)


@pytest.mark.parametrize('base_form, person, number, expected', [
    ('aimer', FIRST, SINGULAR, 'aime'),
    ('aimer', SECOND, SINGULAR, 'aimes'),
    ('aimer', THIRD, SINGULAR, 'aime'),
    ('aimer', FIRST, PLURAL, 'aimons'),
    ('aimer', SECOND, PLURAL, 'aimez'),
    ('aimer', THIRD, PLURAL, 'aiment'),
    ('finir', FIRST, SINGULAR, 'finis'),
    ('finir', SECOND, SINGULAR, 'finis'),
    ('finir', THIRD, SINGULAR, 'finit'),
    ('finir', FIRST, PLURAL, 'finissons'),
    ('finir', SECOND, PLURAL, 'finissez'),
    ('finir', THIRD, PLURAL, 'finissent'),
    ('voir', FIRST, SINGULAR, 'vois'),
    ('voir', SECOND, SINGULAR, 'vois'),
    ('voir', THIRD, SINGULAR, 'voit'),
    ('voir', FIRST, PLURAL, 'voyons'),
    ('voir', SECOND, PLURAL, 'voyez'),
    ('voir', THIRD, PLURAL, 'voient'),
    ('haïr', FIRST, SINGULAR, 'hais'),
    ('haïr', SECOND, SINGULAR, 'hais'),
    ('haïr', THIRD, SINGULAR, 'hait'),
    ('haïr', FIRST, PLURAL, 'haïssons'),
    ('haïr', SECOND, PLURAL, 'haïssez'),
    ('haïr', THIRD, PLURAL, 'haïssent'),
    ('vendre', FIRST, SINGULAR, 'vends'),
    ('vendre', SECOND, SINGULAR, 'vends'),
    ('vendre', THIRD, SINGULAR, 'vend'),
    ('vendre', FIRST, PLURAL, 'vendons'),
    ('vendre', SECOND, PLURAL, 'vendez'),
    ('vendre', THIRD, PLURAL, 'vendent'),
])
def test_build_present_verb(morph_rules_fr, base_form, person, number, expected):
    assert morph_rules_fr.build_present_verb(base_form, person, number) == expected


def test_imperfect_pres_part_radical_elt_has_imparfait_radical(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('être', category=VERB)
    radical = morph_rules_fr.get_imperfect_pres_part_radical(
        verb, base_word=None, base_form='être')
    assert radical == 'ét'


def test_imperfect_pres_part_radical_elt_has_no_imparfait_radical(
        lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('être', category=VERB)
    infl_verb = verb.inflex(verb, person=FIRST)
    infl_verb.features = {}
    radical = morph_rules_fr.get_imperfect_pres_part_radical(
        infl_verb, base_word=verb, base_form='être')
    assert radical == 'ét'


def test_imperfect_pres_part_radical_elt_has_person1s(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('avoir', category=VERB)
    radical = morph_rules_fr.get_imperfect_pres_part_radical(
        verb, base_word=verb, base_form='avoir')
    assert radical == 'av'


def test_imperfect_pres_part_radical_base_word_has_person1s(
        lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('avoir', category=VERB)
    infl_verb = verb.inflex(verb, person=FIRST)
    infl_verb.features = {}
    radical = morph_rules_fr.get_imperfect_pres_part_radical(
        infl_verb, base_word=verb, base_form='avoir')
    assert radical == 'av'


def test_imperfect_pres_part_radical_unexisting_verb(
        lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('kiffer', category=VERB)  # will be inserted
    infl_verb = verb.inflex(verb, person=FIRST)
    infl_verb.features = {}
    radical = morph_rules_fr.get_imperfect_pres_part_radical(
        infl_verb, base_word=verb, base_form='kiffer')
    assert radical == 'kiff'


@pytest.mark.parametrize('gender, number, expected', [
    (MASCULINE, SINGULAR, 'amusant'),
    (FEMININE, SINGULAR, 'amusante'),
    (MASCULINE, PLURAL, 'amusants'),
    (FEMININE, PLURAL, 'amusantes'),
])
def test_realise_verb_participle_or_gerund_used_as_adjective(
        lexicon_fr, morph_rules_fr, gender, number, expected):
    verb = lexicon_fr.first('amuser', category=VERB)
    gerund_or_present_part = morph_rules_fr.realise_verb_present_participle_or_gerund(
        verb, base_word=verb, base_form='amuser', gender=gender, number=number)
    assert gerund_or_present_part == expected


def test_realise_verb_participle_or_gerund(lexicon_fr, morph_rules_fr):
    verb = lexicon_fr.first('être', category=VERB)
    gerund_or_present_part = morph_rules_fr.realise_verb_present_participle_or_gerund(
        verb, base_word=verb, base_form='être', gender=None, number=None)
    assert gerund_or_present_part == 'étant'


@pytest.mark.parametrize('base_form, expected', [
    ('manger', 'mangé'),
    ('vouloir', 'voulu'),
    ('finir', 'fini'),
    ('permettre', 'permis'),
    ('vendre', 'vendu'),
])
def test_build_verb_past_participle(morph_rules_fr, base_form, expected):
    assert morph_rules_fr.build_verb_past_participle(base_form) == expected


@pytest.mark.parametrize('base_form, gender, number, expected', [
    ('être', None, None, 'été'),
    ('kiffer', None, None, 'kiffé'),
    ('manger', FEMININE, SINGULAR, 'mangée'),
    ('manger', FEMININE, PLURAL, 'mangées'),
    ('abattre', FEMININE, SINGULAR, 'abattue'),  # has a feminine past participle
    ('abattre', FEMININE, PLURAL, 'abattues'),  # idem
])
def test_realise_verb_past_participle(
        lexicon_fr, morph_rules_fr, base_form, gender, number, expected):
    verb = lexicon_fr.first(base_form, category=VERB)
    past_participle = morph_rules_fr.realise_verb_past_participle(
        verb, base_word=verb, base_form=base_form, gender=gender, number=number)
    assert past_participle == expected


@pytest.mark.parametrize('base_form, person, number, expected', [
    ('aimer', FIRST, SINGULAR, 'aime'),
    ('aimer', SECOND, SINGULAR, 'aimes'),
    ('aimer', THIRD, SINGULAR, 'aime'),
    ('aimer', FIRST, BOTH, 'aime'),
    ('aimer', SECOND, BOTH, 'aimes'),
    ('aimer', THIRD, BOTH, 'aime'),
    ('aimer', FIRST, PLURAL, 'aimions'),
    ('aimer', SECOND, PLURAL, 'aimiez'),
    ('aimer', THIRD, PLURAL, 'aiment'),
])
def test_build_subjunctive_verb(morph_rules_fr, base_form, person, number, expected):
    assert morph_rules_fr.build_subjunctive_verb(base_form, person, number) == expected


@pytest.mark.parametrize('base_form, person, number, expected', [
    # irregular, from lexicon
    ('aller', FIRST, SINGULAR, 'aille'),
    ('aller', SECOND, SINGULAR, 'ailles'),
    ('aller', THIRD, SINGULAR, 'aille'),
    ('aller', FIRST, BOTH, 'aille'),
    ('aller', SECOND, BOTH, 'ailles'),
    ('aller', THIRD, BOTH, 'aille'),
    ('aller', FIRST, PLURAL, 'allions'),
    ('aller', SECOND, PLURAL, 'alliez'),
    ('aller', THIRD, PLURAL, 'aillent'),
    # regular, from building rules
    ('aimer', FIRST, SINGULAR, 'aime'),
    ('aimer', SECOND, SINGULAR, 'aimes'),
    ('aimer', THIRD, SINGULAR, 'aime'),
    ('aimer', FIRST, BOTH, 'aime'),
    ('aimer', SECOND, BOTH, 'aimes'),
    ('aimer', THIRD, BOTH, 'aime'),
    ('aimer', FIRST, PLURAL, 'aimions'),
    ('aimer', SECOND, PLURAL, 'aimiez'),
    ('aimer', THIRD, PLURAL, 'aiment'),
])
def test_realise_verb_subjunctive(
        lexicon_fr, morph_rules_fr, base_form, person, number, expected):
    verb = lexicon_fr.first(base_form, category=VERB)
    subj = morph_rules_fr.realise_verb_subjunctive(
        verb, base_word=verb, base_form=base_form, number=number, person=person)
    assert subj == expected


@pytest.mark.parametrize('base_form, person, number, expected', [
    ('aller', FIRST, SINGULAR, None),
    ('aller', SECOND, SINGULAR, 'va'),
    ('aller', THIRD, SINGULAR, None),
    ('aller', FIRST, BOTH, None),
    ('aller', SECOND, BOTH, 'va'),
    ('aller', THIRD, BOTH, None),
    ('aller', FIRST, PLURAL, 'allons'),
    ('aller', SECOND, PLURAL, 'allez'),
    ('aller', THIRD, PLURAL, None),
    ('manger', FIRST, SINGULAR, None),
    ('manger', SECOND, SINGULAR, 'mange'),
    ('manger', THIRD, SINGULAR, None),
    ('manger', FIRST, BOTH, None),
    ('manger', SECOND, BOTH, 'mange'),
    ('manger', THIRD, BOTH, None),
    ('manger', FIRST, PLURAL, 'mangeons'),
    ('manger', SECOND, PLURAL, 'mangez'),
    ('manger', THIRD, PLURAL, None),
])
def test_realise_verb_imperative(
        lexicon_fr, morph_rules_fr, base_form, person, number, expected):
    verb = lexicon_fr.first(base_form, category=VERB)
    imp = morph_rules_fr.realise_verb_imperative(
        verb, base_word=verb, base_form=base_form, number=number, person=person)
    assert imp == expected


@pytest.mark.parametrize('base_form, person, number, expected', [
    # irregular: from lexicon
    ('aller', FIRST, SINGULAR, 'vais'),
    ('aller', SECOND, SINGULAR, 'vas'),
    ('aller', THIRD, SINGULAR, 'va'),
    ('aller', FIRST, BOTH, 'vais'),
    ('aller', SECOND, BOTH, 'vas'),
    ('aller', THIRD, BOTH, 'va'),
    ('aller', FIRST, PLURAL, 'allons'),
    ('aller', SECOND, PLURAL, 'allez'),
    ('aller', THIRD, PLURAL, 'vont'),
    # regular: from rules
    ('vendre', FIRST, SINGULAR, 'vends'),
    ('vendre', SECOND, SINGULAR, 'vends'),
    ('vendre', THIRD, SINGULAR, 'vend'),
    ('vendre', FIRST, BOTH, 'vends'),
    ('vendre', SECOND, BOTH, 'vends'),
    ('vendre', THIRD, BOTH, 'vend'),
    ('vendre', FIRST, PLURAL, 'vendons'),
    ('vendre', SECOND, PLURAL, 'vendez'),
    ('vendre', THIRD, PLURAL, 'vendent'),
])
def test_realise_verb_present(
        lexicon_fr, morph_rules_fr, base_form, person, number, expected):
    verb = lexicon_fr.first(base_form, category=VERB)
    imp = morph_rules_fr.realise_verb_present(
        verb, base_word=verb, base_form=base_form, number=number, person=person)
    assert imp == expected


@pytest.mark.parametrize('word, expected', [
    ('envoyer', 'enverr'),  # has a future_radical feature
    ('employer', 'emploier'),  # ends with 'yer'
    ('amener', 'amèn'),
    ('manger', 'manger'),  # does not correspond to anything special
])
def test_get_conditional_or_future_radical(lexicon_fr, morph_rules_fr, word, expected):
    verb = lexicon_fr.first(word, category=VERB)
    radical = morph_rules_fr.get_conditional_or_future_radical(
        verb, base_form=word, base_word=verb)
    assert radical == expected


@pytest.mark.parametrize('radical, person, number, expected', [
    ('aimer', FIRST, SINGULAR, 'aimerai'),
    ('aimer', SECOND, SINGULAR, 'aimeras'),
    ('aimer', THIRD, SINGULAR, 'aimera'),
    ('aimer', FIRST, BOTH, 'aimerai'),
    ('aimer', SECOND, BOTH, 'aimeras'),
    ('aimer', THIRD, BOTH, 'aimera'),
    ('aimer', FIRST, PLURAL, 'aimerons'),
    ('aimer', SECOND, PLURAL, 'aimerez'),
    ('aimer', THIRD, PLURAL, 'aimeront'),
])
def test_build_verb_future(morph_rules_fr, radical, person, number, expected):
    future = morph_rules_fr.build_future_verb(radical=radical, number=number, person=person)
    assert future == expected


@pytest.mark.parametrize('radical, person, number, expected', [
    ('aimer', FIRST, SINGULAR, 'aimerais'),
    ('aimer', SECOND, SINGULAR, 'aimerais'),
    ('aimer', THIRD, SINGULAR, 'aimerait'),
    ('aimer', FIRST, BOTH, 'aimerais'),
    ('aimer', SECOND, BOTH, 'aimerais'),
    ('aimer', THIRD, BOTH, 'aimerait'),
    ('aimer', FIRST, PLURAL, 'aimerions'),
    ('aimer', SECOND, PLURAL, 'aimeriez'),
    ('aimer', THIRD, PLURAL, 'aimeraient'),
])
def test_build_verb_conditional(morph_rules_fr, radical, person, number, expected):
    cond = morph_rules_fr.build_conditional_verb(
        radical=radical, number=number, person=person)
    assert cond == expected


@pytest.mark.parametrize('radical, person, number, expected', [
    ('aimer', FIRST, SINGULAR, 'aimerais'),
    ('aimer', SECOND, SINGULAR, 'aimerais'),
    ('aimer', THIRD, SINGULAR, 'aimerait'),
    ('aimer', FIRST, BOTH, 'aimerais'),
    ('aimer', SECOND, BOTH, 'aimerais'),
    ('aimer', THIRD, BOTH, 'aimerait'),
    ('aimer', FIRST, PLURAL, 'aimerions'),
    ('aimer', SECOND, PLURAL, 'aimeriez'),
    ('aimer', THIRD, PLURAL, 'aimeraient'),
])
def test_build_verb_past(morph_rules_fr, radical, person, number, expected):
    past = morph_rules_fr.build_past_verb(
        radical=radical, number=number, person=person)
    assert past == expected


@pytest.mark.parametrize('word, tense, form, gender, person, number, expected', [
    ('aimer', PRESENT, INDICATIVE, None, FIRST, SINGULAR, 'aime'),
    ('aimer', PRESENT, INDICATIVE, MASCULINE, FIRST, SINGULAR, 'aime'),
    ('aimer', FUTURE, INDICATIVE, MASCULINE, FIRST, SINGULAR, 'aimerai'),
    ('aimer', PAST, INDICATIVE, MASCULINE, FIRST, SINGULAR, 'aimais'),
    ('aimer', CONDITIONAL, INDICATIVE, MASCULINE, FIRST, SINGULAR, 'aimerais'),
    ('aimer', None, BARE_INFINITIVE, MASCULINE, FIRST, SINGULAR, 'aimer'),
    ('aimer', None, INFINITIVE, MASCULINE, FIRST, SINGULAR, 'aimer'),
    ('aimer', None, PRESENT_PARTICIPLE, None, FIRST, SINGULAR, 'aimant'),
    ('aimer', None, PRESENT_PARTICIPLE, MASCULINE, FIRST, SINGULAR, 'aimant'),
    ('aimer', None, PRESENT_PARTICIPLE, FEMININE, FIRST, SINGULAR, 'aimante'),
    ('aimer', None, GERUND, None, FIRST, SINGULAR, 'aimant'),
    ('aimer', None, GERUND, MASCULINE, FIRST, SINGULAR, 'aimant'),
    ('aimer', None, GERUND, FEMININE, FIRST, SINGULAR, 'aimante'),
    ('aimer', None, PAST_PARTICIPLE, None, FIRST, SINGULAR, 'aimé'),
    ('aimer', None, PAST_PARTICIPLE, MASCULINE, FIRST, SINGULAR, 'aimé'),
    ('aimer', None, PAST_PARTICIPLE, FEMININE, FIRST, SINGULAR, 'aimée'),
    ('aimer', None, SUBJUNCTIVE, FEMININE, FIRST, SINGULAR, 'aime'),
    ('aimer', None, IMPERATIVE, FEMININE, FIRST, PLURAL, 'aimons'),
])
def test_morph_verb(
        lexicon_fr, morph_rules_fr, word, tense, form, gender, person, number, expected):
    verb = lexicon_fr.first(word, category=VERB)
    verb.features.update({
        GENDER: gender,
        TENSE: tense,
        NUMBER: number,
        PERSON: person,
        FORM: form,
    })
    realised = morph_rules_fr.morph_verb(verb, base_word=verb)
    assert isinstance(realised, StringElement)
    assert realised.realisation == expected
