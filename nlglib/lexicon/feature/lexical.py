# encoding: utf-8

"""Definition of lexical features."""

from __future__ import unicode_literals


# This feature is used to map an acronym element to the full forms of the
# acronym.
# Expected type: list(WordElement)
# Created by: Lexicons that support acronyms should set this feature.
# Used by: No processors currently use this feature
# Applies to: any lexical item
ACRONYM_OF = "acronym_of"

# This feature is used to map a word to its acronyms.
# Expected type: list(WordElement)
# Created by: Lexicons that support acronyms should set this feature.
# Used by: No processors currently use this feature.
# Applies to: Any lexical item.
ACRONYMS = "acronyms"

# This feature is used to list all the possible inflectional variants of a
# word. For example, the word 'fish' can be both 'uncount'
# (plural: 'fish') and 'reg' (plural: 'fishes').
# Expected type: list(String)
# Created by: Lexicons that support inflectional variants should set
# this feature.
# Used by: No processors currently use this feature.
# Applies to: Any lexical item.
INFLECTIONS = "infl"

# Desc: This feature is used to specify, for a given word, what its default
# inflectional variant is, if more than one is possible.
# Expected type: String
# Created by: Lexicons that support multiple inflectional variants should
# set this feature.
# Used by: MorphologyProcessor.
# Applies to: Nouns and verbs.
DEFAULT_INFL = "default_infl"

# This feature is used to specify the spelling variants of a word.
# Expected type: list(String)
# Created by: Lexicons that support multiple spelling variants should set this
# feature.
# Used by: No processors currently use this feature.
# Applies to: Any lexical item.
SPELL_VARS = "spell_vars"

# This feature is used to specify the default spelling variant of a word,
# if it has more than one.
# Expected type: String
# Created by: Lexicons that support multiple spelling variants should set this
# feature.
# Used by: MorphologyProcessor
# Applies to: Any lexical item.
DEFAULT_SPELL = "default_spell"

# This feature is used to define the base form for phrases and words.
# Expected type: String
# Created by: The lexicon accessor also creates the feature when looking up
# words in the lexicon. Sometimes the phrase factory sets this feature as well,
# as an approximate realisation for debuggin purposes
# Used by: The morphology processor uses the base form in its simple rules for
# determining word inflection. The morphology processor and syntax
# processor also use the base form for lexicon look ups if the base word
# has not been set. Base forms on phrases are purely to aid debugging.
# Applies to: Phrases and words.
BASE_FORM = "base_form"

# This feature is used for determining the position of adjectives. Setting
# this value to true means that the adjective can occupy the
# classifying position.
# Expected type: bool
# Created by: Any lexicon that supports adjective positioning.
# Used by: The syntax processor to determine the ordering of adjectives.
# Applies to: Adjectives within noun phrases.
CLASSIFYING = "classifying"

#
#    *
#    * This feature is used for determining the position of adjectives. Setting
#    * this value to true means that the adjective can occupy the
#    * colour position.
#    * </p>
#    *
#    *
#    * Feature name
#    * colour
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any lexicon that supports adjective positioning.
#    *
#    *
#    * Used by
#    * The syntax processor to determine the ordering of adjectives.
#    *
#    *
#    * Applies to
#    * Adjectives within noun phrases.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
COLOUR = "colour"

#
#    *
#    * This feature gives the comparative form for adjectives and adverbs. For
#    * example, dizzier is the comparative form of dizzy,
#    * fatter is the comparative form of fat and
#    * earlier is the comparative form of early.
#    * </p>
#    *
#    *
#    * Feature name
#    * comparative
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * Can be created automatically by the lexicon or added manually by
#    * users.
#    *
#    *
#    * Used by
#    * The morphology processor uses this information to correctly inflect
#    * words.
#    *
#    *
#    * Applies to
#    * Adjectives and adverbs only.
#    *
#    *
#    * Default</b   * null
#    *
#    * </table>
#
COMPARATIVE = "comparative"

#
#    *
#    * This feature determines if a verb is ditransitive, meaning that it can
#    * have a subject, direct object and indirect object. For example in the
#    * phrase he gave Mary ten pounds, the verb give has three
#    * components: the subject is the person doing the giving (he), the
#    * direct object is the object being passed (ten pounds) and the
#    * indirect object is the recipient (Mary).
#    * </p>
#    *
#    *
#    * Feature name
#    * ditransitive
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * The feature is set by the lexicon if it supports the recording of the
#    * transitive nature of verbs.
#    *
#    *
#    * Used by
#    * The ditransitive value is currently not used.
#    *
#    *
#    * Applies to
#    * Verbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
DITRANSITIVE = "ditransitive"

#
#    *
#    * This feature determines whether a noun is masculine, feminine or neuter
#    * in nature.
#    * </p>
#    *
#    *
#    * Feature name
#    * gender
#    *
#    *
#    * Expected type
#    * Gender
#    *
#    *
#    * Created by
#    * The phrase factory creates the gender of pronouns when creating
#    * phrases and on all nouns within a noun phrase.
#    *
#    *
#    * Used by
#    * The syntax processor ensures that the head noun in a noun phrase has
#    * a gender matching that applied to the phrase as a whole. The morphology
#    * processor uses gender to determine the appropriate form for pronouns and
#    * for setting the form of some verbs.
#    *
#    *
#    * Applies to
#    * Specifically it applies to nouns and pronouns but the feature is also
#    * written to noun phrases and verbs.
#    *
#    *
#    * Default</b   * Gender.NEUTER
#    *
#    * </table>
#
GENDER = "gender"

#
#    *
#    * This flag determines if an adverb is an intensifier, such as
#    * very.
#    * </p>
#    *
#    *
#    * Feature name
#    * intensifier
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * The information is read from Lexicons that support this feature.
#    *
#    *
#    * Used by
#    * Currently not used.
#    *
#    *
#    * Applies to
#    * Adverbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE.
#    *
#    * </table>
#
INTENSIFIER = "intensifier"

#
#    *
#    * This flag highlights a verb that can only take a subject and no objects.
#    * </p>
#    *
#    *
#    * Feature name
#    * intransitive
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * The information is read from Lexicons that support this feature.
#    *
#    *
#    * Used by
#    * Currently not used.
#    *
#    *
#    * Applies to
#    * Verbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE.
#    *
#    * </table>
#
INTRANSITIVE = "intransitive"

#
#    *  This feature represents non-countable nouns such as mud,
#    * sand and water. </p>
#    * Feature name nonCount
#    * Expected type Boolean
#    * Created by Supporting lexicons.
#    * Used by The morphology processor will not pluralise
#    * non-countable nouns.   Applies to Nouns
#    * only.   Default</b   * Boolean.FALSE.  </table>
#
#  public static final String NON_COUNT = "nonCount";
#
#    *
#    * This feature gives the past tense form of a verb. For example, the past
#    * tense of eat is ate, the past tense of walk is
#    * walked.
#    * </p>
#    *
#    *
#    * Feature name
#    * past
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * All supporting lexicons but can be set by the user for irregular
#    * cases.
#    *
#    *
#    * Used by
#    * The morphology processor uses this feature to correctly inflect
#    * verbs. This feature will be looked at first before any reference to
#    * lexicons or morphology rules.
#    *
#    *
#    * Applies to
#    * Verbs and verb phrases only.
#    *
#    *
#    * Default</b   * null.
#    *
#    * </table>
#
PAST = "past"

#
#    *
#    * This feature gives the past participle tense form of a verb. For many
#    * verbs the past participle is exactly the same as the past tense, for
#    * example, the verbs talk, walk and say have
#    * past tense and past participles of talked, walked and
#    * said. Contrast this with the verbs do, eat and
#    * sing. The past tense of these verbs is did,
#    * ate and sang respectively. while the respective past
#    * participles are done, eaten and sung
#    * </p>
#    *
#    *
#    * Feature name
#    * pastParticiple
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * All supporting lexicons but can be set by the user for irregular
#    * cases.
#    *
#    *
#    * Used by
#    * The morphology processor uses this feature to correctly inflect
#    * verbs. This feature will be looked at first before any reference to
#    * lexicons or morphology rules.
#    *
#    *
#    * Applies to
#    * Verbs and verb phrases only.
#    *
#    *
#    * Default</b   * null.
#    *
#    * </table>
#
PAST_PARTICIPLE = "pastParticiple"

#
#    *
#    * This feature gives the plural form of a noun. For example, the plural of
#    * dog is dogs and the plural of sheep is
#    * sheep.
#    * </p>
#    *
#    *
#    * Feature name
#    * plural
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * All supporting lexicons but can be set by the user for irregular
#    * cases.
#    *
#    *
#    * Used by
#    * The morphology processor uses this feature to correctly inflect
#    * plural nouns. This feature will be looked at first before any reference
#    * to lexicons or morphology rules.
#    *
#    *
#    * Applies to
#    * Nouns only.
#    *
#    *
#    * Default</b   * null.
#    *
#    * </table>
#
PLURAL = "plural"

#
#    *
#    * This flag is set on adjectives that can also be used as a predicate. For
#    * example happy.
#    * </p>
#    *
#    *
#    * Feature name
#    * predicative
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any supporting lexicon.
#    *
#    *
#    * Used by
#    * Currently not used.
#    *
#    *
#    * Applies to
#    * Adjectives only.
#    *
#    *
#    * Default</b   * Boolean.FALSE.
#    *
#    * </table>
#
PREDICATIVE = "predicative"

#
#    *
#    * This feature gives the present participle form of a verb. For example,
#    * the present participle form of eat is eating and the
#    * present participle form of walk is walking.
#    * </p>
#    *
#    *
#    * Feature name
#    * presentParticiple
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * All supporting lexicons but can be set by the user for irregular
#    * cases.
#    *
#    *
#    * Used by
#    * The morphology processor uses this feature to correctly inflect
#    * verbs. This feature will be looked at first before any reference to
#    * lexicons or morphology rules.
#    *
#    *
#    * Applies to
#    * Verbs only.
#    *
#    *
#    * Default</b   * null.
#    *
#    * </table>
#
PRESENT_PARTICIPLE = "presentParticiple"

#
#    *
#    * This feature gives the present third person singular form of a verb. For
#    * example, the present participle form of eat is eats as
#    * in the dog eats. Another example is ran being the
#    * present third person singular form of run as in
#    * John ran home.
#    * </p>
#    *
#    *
#    * Feature name
#    * present3s
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * All supporting lexicons but can be set by the user for irregular
#    * cases.
#    *
#    *
#    * Used by
#    * The morphology processor uses this feature to correctly inflect
#    * verbs. This feature will be looked at first before any reference to
#    * lexicons or morphology rules.
#    *
#    *
#    * Applies to
#    * Verbs only.
#    *
#    *
#    * Default</b   * null.
#    *
#    * </table>
#
PRESENT3S = "present3s"

#
#    *
#    * This flag is used to determine whether a noun is a proper noun, such as a
#    * person's name.
#    * </p>
#    *
#    *
#    * Feature name
#    * proper
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Can be set by supporting lexicons or by the user.
#    *
#    *
#    * Used by
#    * The morphology processor will not pluralise proper nouns.
#    *
#    *
#    * Applies to
#    * Nouns only.
#    *
#    *
#    * Default</b   * Boolean.FALSE.
#    *
#    * </table>
#
PROPER = "proper"

#
#    *
#    * This feature is used for determining the position of adjectives. Setting
#    * this value to true means that the adjective can occupy the
#    * qualitative position.
#    * </p>
#    *
#    *
#    * Feature name
#    * qualitative
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any lexicon that supports adjective positioning.
#    *
#    *
#    * Used by
#    * The syntax processor to determine the ordering of adjectives.
#    *
#    *
#    * Applies to
#    * Adjectives within noun phrases.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
QUALITATIVE = "qualitative"

#
#    *
#    * This flag is set if a pronoun is written in the reflexive form. For
#    * example, myself, yourself, ourselves.
#    * </p>
#    *
#    *
#    * Feature name
#    * isReflexive
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * The phrase factory will recognise personal pronouns in reflexive
#    * form.
#    *
#    *
#    * Used by
#    * The morphology processor will correctly inflect reflexive pronouns.
#    *
#    *
#    * Applies to
#    * Pronouns only.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
REFLEXIVE = "reflexive"

#
#    *
#    * This feature is used to define whether an adverb can be used as a clause
#    * modifier, which are normally applied at the beginning of clauses. For
#    * example, unfortunately.
#    * </p>
#    *
#    *
#    * Feature name
#    * sentenceModifier
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any lexicon that supports this feature.
#    *
#    *
#    * Used by
#    * generic addModifier methods, to decide where to put an adverb
#    *
#    *
#    * Applies to
#    * Adverbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
SENTENCE_MODIFIER = "sentence_modifier"

#
#    *
#    * This feature gives the superlative form for adjectives and adverbs. For
#    * example, fattest is the superlative form of fat and
#    * earliest is the superlative form of early.
#    * </p>
#    *
#    *
#    * Feature name
#    * superlative
#    *
#    *
#    * Expected type
#    * String
#    *
#    *
#    * Created by
#    * Can be created automatically by the lexicon or added manually by
#    * users.
#    *
#    *
#    * Used by
#    * The morphology processor uses this information to correctly inflect
#    * words.
#    *
#    *
#    * Applies to
#    * Adjectives and adverbs only.
#    *
#    *
#    * Default</b   * null
#    *
#    * </table>
#
SUPERLATIVE = "superlative"

#
#    *
#    * This flag highlights a verb that can only take a subject and an object.
#    * </p>
#    *
#    *
#    * Feature name
#    * transitive
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any lexicon supporting this feature.
#    *
#    *
#    * Used by
#    * Currently not used.
#    *
#    *
#    * Applies to
#    * Verbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE.
#    *
#    * </table>
#
TRANSITIVE = "transitive"

#
#    *
#    * This feature is used to define whether an adverb can be used as a verb
#    * modifier, which are normally added in a phrase before the verb itself.
#    * For example, quickly.
#    * </p>
#    *
#    *
#    * Feature name
#    * verbModifier
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * Any lexicon that supports this feature.
#    *
#    *
#    * Used by
#    * generic addModifier methods, to decide where to put an adverb.
#    *
#    *
#    * Applies to
#    * Adverbs only.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
VERB_MODIFIER = "verb_modifier"

#
#    *
#    * This feature determines if the pronoun is an expletive or not. Expletive
#    * pronouns are usually it or there in sentences such as:<br>
#    * <b>It</b> is raining now.<br>
#    * <b>There</b> are ten desks in the room.
#    * </p>
#    *
#    *
#    * Feature name
#    * isExpletive
#    *
#    *
#    * Expected type
#    * Boolean
#    *
#    *
#    * Created by
#    * The feature needs to be set by the user.
#    *
#    *
#    * Used by
#    * The syntax processor uses the expletive on verb phrases for
#    * determining the correct number agreement.
#    *
#    *
#    * Applies to
#    * Certain pronouns when used as subjects of verb phrases.
#    *
#    *
#    * Default</b   * Boolean.FALSE
#    *
#    * </table>
#
EXPLETIVE_SUBJECT = "expletive_subject"
