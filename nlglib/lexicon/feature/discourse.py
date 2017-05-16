# encoding: utf-8

"""
An enumeration representing the grammatical function that an element might
take. The discourse function is recorded under the
Feature.DISCOURSE_FUNCTION feature and applies to any type of
NLGElement.

"""

from __future__ import unicode_literals

# Auxiliaries are the additional verbs added to a verb phrase to alter the
# meaning being described. For public static final String example =
# "example"; <em>will</em> can be added as an auxiliary to a verb phrase to
# represent the future tense of the public static final String verb =
# "verb"; <em>John <b>will</b> kiss Mary</em>.
AUXILIARY = "auxiliary"

# Complements are additional components that are required to complement the
# meaning of a sentence. For public static final String example =
# "example"; <em>put the bread <b>on the table</b></em> requires the
# complement <em>on the table</em> to make the clause meaningful.
COMPLEMENT = "complement"

# A conjunction is a word that links items together in a coordinated
# phrase. The most common conjunctions are <em>and</em> and <em>but</em>.
CONJUNCTION = "conjunction"

# Cue phrases are added to sentence to indicate document structure or flow.
# They normally do not add any semantic information to the phrase. For
# public static final String example = "example";
# <em><b>Firstly</b>, let me just say it is an honour to be here.</em>
# <em><b>Incidentally</b>, John kissed Mary last night.</em>
CUE_PHRASE = "cue_phrase"

# Front modifiers are modifiers that apply to clauses. They are placed in
# the syntactical structure after the cue phrase but before the subject.
# For public static final String example = "example";
# <em>However, <b>last night</b> John kissed Mary.</em>
FRONT_MODIFIER = "front_modifier"

# This represents the main item of the phrase. For verb public static final
# String phrases = "phrases"; the head will be the main verb. For noun
# public static final String phrases = "phrases"; the head will be the
# subject noun. For public static final String adjective = "adjective";
# adverb and prepositional public static final String phrases = "phrases";
# the head will be the public static final String adjective = "adjective";
# adverb and preposition respectively.
HEAD = "head"

# This is the indirect object of a verb phrase or an additional object that
# is affected by the action performed. This is typically the recipient of
# <em>give</em>. For public static final String example = "example"; Mary
# is the indirect object in the phrase
# <em>John gives <b>Mary</b> the flower</em>.
INDIRECT_OBJECT = "indirect_object"

# This is the object of a verb phrase and represents the item that the
# action is performed upon. For public static final String example =
# "example"; the flower is the object in the phrase
# <em>John gives Mary <b>the flower</b></em>.
OBJECT = "object"

# Pre-modifiers, typically adjectives and public static final String
# adverbs = "adverbs"; appear before the head of a phrase. They can apply
# to noun phrases and verb phrases. For public static final String example
# = "example"; <em>the <b>beautiful</b> woman</em>,
# <em>the <b>ferocious</b> dog</em>.
PRE_MODIFIER = "pre_modifier"

# Post-modifiers, typically adjectives and public static final String
# adverbs = "adverbs"; are added after the head of the phrase. For public
# static final String example = "example";
# <em>John walked <b>quickly</b></em>.
POST_MODIFIER = "post_modifier"

# The public static final String specifier = "specifier"; otherwise known
# as the public static final String determiner = "determiner"; is a word
# that can be placed before a noun in a noun phrase. Example specifiers
# include: <em>the</em>, <em>some</em>, <em>a</em> and <em>an</em> as well
# as the personal pronouns such as <em>my</em>, <em>your</em>,
SPECIFIER = "specifier"

# This is the subject of a verb phrase and represents the entity performing
# the action. For public static final String example = "example"; John is
# the subject in the phrase <em><b>John</b> gives Mary the flower.</em>
SUBJECT = "subject"

# The verb phrase highlights the part of a clause that forms the verb
# phrase. Verb phrases can be formed of a single verb or from a verb with a
# public static final String particle = "particle"; such as <em>kiss</em>,
# <em>talk</em>, <em>bark</em>, <em>fall down</em>, <em>pick up</em>.
VERB_PHRASE = "verb_phrase"
