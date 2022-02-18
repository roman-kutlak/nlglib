# encoding: utf-8

"""Definition of form-related features."""


# The bare infinitive is the base form of the verb.
BARE_INFINITIVE = "bare_infinitive"

# The conditional form of a verb is the one used when the grammatical
# mood is one of expressing a request or describing situations that are uncertain.
# For example, <em>I <b>would close</b> the door if you let me.</em>
CONDITIONAL = 'conditional'


# In English, the gerund form refers to the usage of a verb as a noun. For
# example, <em>I like <b>swimming</b></em>. In more general terms, gerunds
# are usually formed from the base word with <em>-ing</em> added to the end.
GERUND = "gerund"


# The imperative form of a verb is the one used when the grammatical
# mood is one of expressing a command or giving a direct request.
# For example, <em><b>Close</b> the door.</em>
IMPERATIVE = "imperative"


# The infinitive form represents the base form of the verb, with our
# without the particle <em>to</em>. For example, <em>do</em> and
# <em>to do</em> are both infinitive forms of <em>do</em>.
INFINITIVE = "infinitive"

# The indicative form of a verb is used when the grammatical
# mood is one of expressing a statement or a fact.
# For example, <em>Whales <b>are</b> mammals, not fish.</em>
INDICATIVE = "indicative"


# Normal form represents the base verb.
# For example, <em>kiss</em>, <em>walk</em>, <em>bark</em>, <em>eat</em>.
NORMAL = "normal"


# Most verbs will have only a single form for the past tense. However, some
# verbs will have two forms, one for the simple past tense and one for the
# past participle (also knowns as passive participle or perfect
# participle). The part participle represents the second of these two
# forms. For example, the verb <em>eat</em> has the simple past form of
# <em>ate</em> and also the past participle form of <em>eaten</em>. Another
# example, is <em>write</em>, <em>wrote</em> and <em>written</em>.
PAST_PARTICIPLE = "past_participle"


# The present participle is identical in form to the gerund and is normally
# used in the active voice. However, the gerund is meant to highlight a
# verb being used as a noun. The present participle remains as a verb. For
# example, <em>Jim was <b>sleeping</b></em>.
PRESENT_PARTICIPLE = "present_participle"


# The subjunctive form of a verb is used when the grammatical
# mood is one of expressing a wish or possibility.
# For example, <em>Whales <b>are</b> mammals, not fish.</em>
# <em>I wish I <b>were</b> more productive.</em>
SUBJUNCTIVE = "subjunctive"
