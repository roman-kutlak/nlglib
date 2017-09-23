from nlglib.features import person, number, gender
from nlglib.features.category import *
from nlglib.globals import current_lexicon
from nlglib.structures import Element


class Factory(object):
    """Class for creating templates without a lexicon."""

    pos = None
    default_features = {}

    def __init__(self, base_form, features=None, **kwargs):
        self.features = self.default_features.copy()
        self.base_form, features = self.str_or_element(base_form, features)
        self.features.update(features)
        self.features.update(kwargs)

    def __call__(self):
        pos = self.pos or self.__class__.__name__.upper()
        assert pos in TAGS
        rv = current_lexicon.get(self.base_form, pos)
        rv.features.update(self.features)
        return rv

    @staticmethod
    def str_or_element(word, features=None):
        features = features or {}
        if isinstance(word, str):
            return word, features
        elif isinstance(word, Element):
            tmp = str(word)
            features.update(word.features)
            return tmp, features
        else:
            return str(word), features


class Any(Factory):
    pass


class Adjective(Factory):
    pass


class Adverb(Factory):
    pass


class Auxiliary(Factory):
    pass


class Complementiser(Factory):
    pass


class Conjunction(Factory):
    pass


class Determiner(Factory):
    pass


class Interjection(Factory):
    pass


class Modal(Factory):
    pass


class Noun(Factory):
    pos = 'NOUN'


class Numeral(Factory):
    pass


class Particle(Factory):
    pass


class Preposition(Factory):
    pass


class Pronoun(Factory):
    pass


class Symbol(Factory):
    pass


class Verb(Factory):
    pos = 'VERB'


# functions for creating phrases (mostly based on Penn Treebank tags)
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
# scroll down for a list of tags

# 12.	NN      Noun, singular or mass
# 13.	NNS     Noun, plural
# 14.	NNP     Proper noun, singular
# 15.	NNPS	Proper noun, plural


class NN(Noun):
    default_features = {'NUMBER': number.SINGULAR}


class NNS(Noun):
    default_features = {'NUMBER': number.PLURAL}


class NNP(Noun):
    default_features = {
        'NUMBER': number.SINGULAR,
        'PROPER': 'true'
    }


class NNPS(Noun):
    default_features = {
        'NUMBER': number.PLURAL,
        'PROPER': 'true'
    }


class Male(Noun):
    default_features = {
        'NUMBER': number.SINGULAR,
        'PROPER': 'true',
        'GENDER': gender.MASCULINE
    }


class Female(Noun):
    default_features = {
        'NUMBER': number.SINGULAR,
        'PROPER': 'true',
        'GENDER': gender.FEMININE
    }


class Neuter(Noun):
    default_features = {
        'NUMBER': number.SINGULAR,
        'PROPER': 'true',
        'GENDER': gender.NEUTER
    }


# phrases


def NP(spec, *mods_and_head, features=None):
    """ Create a complex noun phrase where the first arg is determiner, then
    modifiers and head is last. Determiner can be None.
    The determiner can be omitted if the NP consists of the head noun only.
    NP('the', 'brown', 'wooden', 'table')

    """
    from nlglib.structures import NounPhrase

    if len(mods_and_head) == 0:
        words = [spec]
        spec = None
    else:
        words = list(mods_and_head)
    if spec is None:
        return NounPhrase(Noun(words[-1]), features=features,
                          premodifiers=[Adjective(x) for x in words[:-1]])
    else:
        return NounPhrase(Noun(words[-1]), Determiner(spec), features=features,
                          premodifiers=[Adjective(x) for x in words[:-1]])


def VP(head, *complements, features=None):
    from nlglib.structures import VerbPhrase
    return VerbPhrase(Verb(head), *complements, features=features)


def PP(head, *complements, features=None):
    from nlglib.structures import PrepositionPhrase
    return PrepositionPhrase(Preposition(head),
                             *complements, features=features)


def AdjP(head, *complements, features=None):
    from nlglib.structures import AdjectivePhrase
    return AdjectivePhrase(Adjective(head), *complements, features=features)


def AdvP(head, *complements, features=None):
    from nlglib.structures import AdverbPhrase
    return AdverbPhrase(Adverb(head), *complements, features=features)
