"""This module contains the basic features used by the library.

If you are defining your own features, use the `Feature` and
`FeatureGroup` classes defined in this package.

"""

from .feature import FeatureGroup

CASE = FeatureGroup(
    'CASE',
    'nominative',
    'accusative',
    'genitive',
    'dative',
    'vocative',
    'locative',
    'instrumental',
    transform='lower'
)

NUMBER = FeatureGroup(
    'NUMBER',
    'singular',
    'plural',
    'both',
    transform='lower'
)

GENDER = FeatureGroup(
    'GENDER',
    'masculine',
    'feminine',
    'neuter',
    transform='lower'
)

# `generic` can be used for pronouns eg 'you' in
PERSON = FeatureGroup(
    'PERSON',
    'first',
    'second',
    'third',
    'generic',
    transform='lower'
)

TENSE = FeatureGroup(
    'TENSE',
    'present',
    'past',
    'future',
    'conditional',
    transform='lower'
)

# The Simple Aspect (Indefinite Aspect)	Example
# simple past tense	            I went
# simple present tense	        I go
# simple future tense	        I will go
# The Perfect Aspect (Completed Aspect)	Example
# past perfect tense	        I had gone
# present perfect tense	        I have gone
# future perfect tense	        I will have gone
# The Progressive Aspect (Continuing Aspect)	Example
# past progressive tense	    I was going
# present progressive tense	    I am going
# future progressive tense	    I will be going
# The Perfect Progressive Aspect	Example
# past perfect progressive tense	I had been going
# present perfect progressive tense	I have been going
# future perfect progressive tense	I will have been going
ASPECT = FeatureGroup(
    'ASPECT',
    'simple',
    'perfect',
    'progressive',
    'perfect_progressive',
    transform='lower'
)

MOOD = FeatureGroup(
    'MOOD',
    'indicative',
    'imperative',
    'subjunctive',
    transform='lower'
)

MODAL = FeatureGroup(
    'MODAL',
    'can', 'could',
    'may', 'might',
    'must', 'ought',
    'shall', 'should',
    'will', 'would',
    transform='lower'
)

VOICE = FeatureGroup(
    'VOICE',
    'active',
    'passive',
    transform='lower'
)

FORM = FeatureGroup(
    'FORM',
    'bare_infinitive',
    'gerund',
    'imperative',
    'infinitive',
    'indicative',
    'past_participle',
    'present_participle',
    transform='lower'
)

INTERROGATIVE_TYPE = FeatureGroup(
    'INTERROGATIVE_TYPE',
    'how',
    'why',
    'where',
    'how_many',
    'yes_no',
    'how_predicate',
    'what_object',
    'what_subject',
    'who_object',
    'who_subject',
    'who_indirect_object',
    transform='lower'
)

REGISTER = FeatureGroup(
    'REGISTER',
    'formal',
    'informal',
    transform='lower'
)

CLAUSE = FeatureGroup(
    'CLAUSE',
    'matrix',
    'subordinate',
    transform='lower'
)

NOUN_TYPE = FeatureGroup(
    'NOUN_TYPE',
    'common',
    'proper',
    transform='lower'
)

PRONOUN_TYPE = FeatureGroup(
    'PRONOUN_TYPE',
    'personal',
    'special_personal',
    'snumeral',
    'possessive',
    'demonstrative',
    'relative',
    'interrogative',
    'indefinite',
    transform='lower'
)

PRONOUN_USE = FeatureGroup(
    'PRONOUN_USE',
    'subjective',
    'objective',
    'reflexive',
    'possessive',
    transform='lower'
)

NEGATED = FeatureGroup(
    'NEGATED',
    'true',
    'false',
)

ELIDED = FeatureGroup(
    'ELIDED',
    'elided',
    'true',
    'false',
)

INFLECTED = FeatureGroup(
    'INFLECTED',
    'true',
    'false',
)


# ######################### Discourse ######################### #


"""
An enumeration representing the grammatical function
that an element might take. The discourse function
is recorded under the feature `DISCOURSE_FUNCTION`
and applies to any type of NLGElement.

"""

DISCOURSE_FUNCTION = FeatureGroup(
    'DISCOURSE_FUNCTION',

    # Auxiliaries are the additional verbs added to a verb phrase to alter the
    # meaning being described. For public static final String example =
    # "example"; <em>will</em> can be added as an auxiliary to a verb phrase to
    # represent the future tense of the public static final String verb =
    # "verb"; <em>John <b>will</b> kiss Mary</em>.
    "auxiliary",

    # Complements are additional components that are required to complement the
    # meaning of a sentence. For public static final String example =
    # "example"; <em>put the bread <b>on the table</b></em> requires the
    # complement <em>on the table</em> to make the clause meaningful.
    "complement",

    # A conjunction is a word that links items together in a coordinated
    # phrase. The most common conjunctions are <em>and</em> and <em>but</em>.
    "conjunction",

    # Cue phrases are added to sentence to indicate document structure or flow.
    # They normally do not add any semantic information to the phrase. For
    # public static final String example = "example";
    # <em><b>Firstly</b>, let me just say it is an honour to be here.</em>
    # <em><b>Incidentally</b>, John kissed Mary last night.</em>
    "cue_phrase",

    # Front modifiers are modifiers that apply to clauses. They are placed in
    # the syntactical structure after the cue phrase but before the subject.
    # For public static final String example = "example";
    # <em>However, <b>last night</b> John kissed Mary.</em>
    "front_modifier",

    # This represents the main item of the phrase. For verb public static final
    # String phrases = "phrases"; the head will be the main verb. For noun
    # public static final String phrases = "phrases"; the head will be the
    # subject noun. For public static final String adjective = "adjective";
    # adverb and prepositional public static final String phrases = "phrases";
    # the head will be the public static final String adjective = "adjective";
    # adverb and preposition respectively.
    "head",

    # This is the indirect object of a verb phrase or an additional object that
    # is affected by the action performed. This is typically the recipient of
    # <em>give</em>. For public static final String example = "example"; Mary
    # is the indirect object in the phrase
    # <em>John gives <b>Mary</b> the flower</em>.
    "indirect_object",

    # This is the object of a verb phrase and represents the item that the
    # action is performed upon. For public static final String example =
    # "example"; the flower is the object in the phrase
    # <em>John gives Mary <b>the flower</b></em>.
    "object",

    # Pre-modifiers, typically adjectives and public static final String
    # adverbs = "adverbs"; appear before the head of a phrase. They can apply
    # to noun phrases and verb phrases. For public static final String example
    # = "example"; <em>the <b>beautiful</b> woman</em>,
    # <em>the <b>ferocious</b> dog</em>.
    "pre_modifier",

    # Post-modifiers, typically adjectives and public static final String
    # adverbs = "adverbs"; are added after the head of the phrase. For public
    # static final String example = "example";
    # <em>John walked <b>quickly</b></em>.
    "post_modifier",

    # The public static final String specifier = "specifier"; otherwise known
    # as the public static final String determiner = "determiner"; is a word
    # that can be placed before a noun in a noun phrase. Example specifiers
    # include: <em>the</em>, <em>some</em>, <em>a</em> and <em>an</em> as well
    # as the personal pronouns such as <em>my</em>, <em>your</em>,
    "specifier",

    # This is the subject of a verb phrase and represents the entity performing
    # the action. For public static final String example = "example"; John is
    # the subject in the phrase <em><b>John</b> gives Mary the flower.</em>
    "subject",

    # The verb phrase highlights the part of a clause that forms the verb
    # phrase. Verb phrases can be formed of a single verb or from a verb with a
    # public static final String particle = "particle"; such as <em>kiss</em>,
    # <em>talk</em>, <em>bark</em>, <em>fall down</em>, <em>pick up</em>.
    "predicate",

    # use lower CASE for constants
    transform='lower'
)

# features that are excluded from equality comparison
NON_COMPARABLE_FEATURES = [DISCOURSE_FUNCTION]

# features that should be transferred on replacement
TRANSFERABLE_FEATURES = [DISCOURSE_FUNCTION]
