# encoding: utf-8

"""Definition of the lexical categories."""


# Lexical categories

#  A default value, indicating an unspecified category.
ANY = "ANY"

#  The element represents a symbol.
SYMBOL = "SYMBOL"

#  A noun element.
NOUN = "NOUN"

#  An adjective element.
ADJECTIVE = "ADJECTIVE"

#  An adverb element.
ADVERB = "ADVERB"

#  A verb element.
VERB = "VERB"

#  A determiner element often referred to as a specifier.
DETERMINER = "DETERMINER"

#  A pronoun element.
PRONOUN = "PRONOUN"

#  A conjunction element.
CONJUNCTION = "CONJUNCTION"

#  A particle element (not in SimpleNLG).
PARTICLE = "PARTICLE"

#  A preposition element.
PREPOSITION = "PREPOSITION"

#  A complementiser element.
COMPLEMENTISER = "COMPLEMENTISER"

#  A modal element.
MODAL = "MODAL"

#  An auxiliary verb element.
AUXILIARY = "AUXILIARY"


# Phrase categories

CLAUSE = "CLAUSE"
ADJECTIVE_PHRASE = "ADJECTIVE_PHRASE"
ADVERB_PHRASE = "ADVERB_PHRASE"
NOUN_PHRASE = "NOUN_PHRASE"
PREPOSITIONAL_PHRASE = "PREPOSITIONAL_PHRASE"
VERB_PHRASE = "VERB_PHRASE"
CANNED_TEXT = "CANNED_TEXT"
COORDINATED_PHRASE = "COORDINATED_PHRASE"

# Document categories

DOCUMENT = 'DOCUMENT'
PARAGRAPH = 'PARAGRAPH'


# Content categories

MSG = 'MSG'
RST = 'RST'


# Groupings for easy lookup

LEXICAL_CATEGORIES = [
    ANY,
    SYMBOL,
    NOUN,
    ADJECTIVE,
    ADVERB,
    VERB,
    DETERMINER,
    PRONOUN,
    CONJUNCTION,
    PARTICLE,
    PREPOSITION,
    COMPLEMENTISER,
    MODAL,
    AUXILIARY,
]

PHRASE_CATEGORIES = [
    CLAUSE,
    ADJECTIVE_PHRASE,
    ADVERB_PHRASE,
    NOUN_PHRASE,
    PREPOSITIONAL_PHRASE,
    VERB_PHRASE,
    CANNED_TEXT,
    COORDINATED_PHRASE,
]

DOCUMENT_CATEGORIES = [
    DOCUMENT,
    PARAGRAPH,
]

CONTENT_CATEGORIES = [
    MSG,
    RST,
]
