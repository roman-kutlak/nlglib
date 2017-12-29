from nlglib.features import NUMBER, GENDER, NOUN_TYPE
from nlglib.features.category import *
from .struct import *


###############################################################################
#                                                                              #
#                      functions for creating word elements                    #
#                                                                              #
###############################################################################


@str_or_element
def Any(word, features=None):
    return Word(word, ANY, features)


@str_or_element
def Adjective(word, features=None):
    return Word(word, ADJECTIVE, features)


@str_or_element
def Adverb(word, features=None):
    return Word(word, ADVERB, features)


@str_or_element
def Auxiliary(word, features=None):
    return Word(word, AUXILIARY, features)


@str_or_element
def Complementiser(word, features=None):
    return Word(word, COMPLEMENTISER, features)


@str_or_element
def Conjunction(word, features=None):
    return Word(word, CONJUNCTION, features)


@str_or_element
def Determiner(word, features=None):
    return Word(word, DETERMINER, features)


@str_or_element
def Determiner(word, features=None):
    return Word(word, DETERMINER, features)


@str_or_element
def Interjection(word, features=None):
    return Word(word, INTERJECTION, features)


@str_or_element
def Modal(word, features=None):
    return Word(word, MODAL, features)


@str_or_element
def Noun(word, features=None):
    return Word(word, NOUN, features)


@str_or_element
def Numeral(word, features=None):
    return Word(word, NUMERAL, features)


@str_or_element
def Particle(word, features=None):
    return Word(word, PARTICLE, features)


@str_or_element
def Preposition(word, features=None):
    return Word(word, PREPOSITION, features)


@str_or_element
def Pronoun(word, features=None):
    return Word(word, PRONOUN, features)


@str_or_element
def Symbol(word, features=None):
    return Word(word, SYMBOL, features)


@str_or_element
def Verb(word, features=None):
    return Word(word, VERB, features)


# functions for creating phrases (mostly based on Penn Treebank tags)
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
# scroll down for a list of tags

# 12.	NN      Noun, singular or mass
# 13.	NNS     Noun, plural
# 14.	NNP     Proper noun, singular
# 15.	NNPS	Proper noun, plural

@str_or_element
def NN(word, features=None):
    return Noun(word, features=features)


@str_or_element
def NNS(word, features=None):
    o = Noun(word, features=features)
    o[NUMBER] = NUMBER.plural
    return o


@str_or_element
def NNP(name, features=None):
    o = Noun(name, features=features)
    o[NOUN_TYPE] = NOUN_TYPE.proper
    return o


@str_or_element
def NNPS(name, features=None):
    o = Noun(name, features=features)
    o[NOUN_TYPE] = NOUN_TYPE.proper
    o[NUMBER] = NUMBER.plural
    return o


@str_or_element
def Male(name, features=None):
    o = Noun(name, features=features)
    o[NOUN_TYPE] = NOUN_TYPE.proper
    o[GENDER] = GENDER.masculine
    return o


@str_or_element
def Female(name, features=None):
    o = Noun(name, features=features)
    o[NOUN_TYPE] = NOUN_TYPE.proper
    o[GENDER] = GENDER.feminine
    return o


# phrases


def NP(spec, *mods_and_head, features=None, **kwargs):
    """ Create a complex noun phrase where the first arg is determiner, then
    modifiers and head is last. Determiner can be None.
    The determiner can be omitted if the NP consists of the head noun only.
    NP('the', 'brown', 'wooden', 'table')

    """
    if len(mods_and_head) == 0:
        words = [spec]
        spec = None
    else:
        words = list(mods_and_head)
    if spec is None:
        return NounPhrase(Noun(words[-1]), features=features,
                          premodifiers=[Adjective(x) for x in words[:-1]], **kwargs)
    else:
        return NounPhrase(Noun(words[-1]), Determiner(spec), features=features,
                          premodifiers=[Adjective(x) for x in words[:-1]], **kwargs)


def VP(head, *complements, features=None, **kwargs):
    return VerbPhrase(Verb(head), *complements, features=features, **kwargs)


def PP(head, *complements, features=None, **kwargs):
    return PrepositionPhrase(Preposition(head),
                             *complements, features=features, **kwargs)


def AdjP(head, *complements, features=None, **kwargs):
    return AdjectivePhrase(Adjective(head), *complements, features=features, **kwargs)


def AdvP(head, *complements, features=None, **kwargs):
    return AdverbPhrase(Adverb(head), *complements, features=features, **kwargs)


def CC(*coordinates, features=None, **kwargs):
    return Coordination(*coordinates, features=features, **kwargs)
