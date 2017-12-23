"""This module contains the basic features used by the library.

If you are defining your own features, use the `Feature` and
`FeatureGroup` classes defined in this package.

"""

from .feature import FeatureGroup


case = FeatureGroup('case',
                    'nominative', 'accusative', 'genitive',
                    'dative', 'vocative', 'locative', 'instrumental')

number = FeatureGroup('number', 'singular', 'plural', 'both')

gender = FeatureGroup('gender', 'masculine', 'feminine', 'neuter')

# `generic` can be used for pronouns eg 'you' in
person = FeatureGroup('person', 'first', 'second', 'third', 'generic')

tense = FeatureGroup('tense', 'present', 'past', 'future', 'conditional')


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
aspect = FeatureGroup('aspect', 'simple', 'perfect', 'progressive', 'perfect progressive')

mood = FeatureGroup('mood', 'indicative', 'imperative', 'subjunctive')

modal = FeatureGroup('modal',
                     'can', 'could',
                     'may', 'might',
                     'must', 'ought',
                     'shall', 'should',
                     'will', 'would')

voice = FeatureGroup('voice', 'active', 'passive')

form = FeatureGroup('form',
                    'bare_infinitive',
                    'gerund',
                    'imperative',
                    'infinitive',
                    'indicative',
                    'past_participle',
                    'present_participle')

interrogative_type = FeatureGroup('interrogative_type',
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
                                  'who_indirect_object')

register = FeatureGroup('register', 'formal', 'informal')

clause = FeatureGroup('clause', 'matrix', 'subordinate')

pronoun_use = FeatureGroup('pronoun_use', 'subjective', 'objective', 'reflexive', 'possessive')

pronoun_type = FeatureGroup('pronoun_type',
                            'personal',
                            'special_personal',
                            'snumeral',
                            'possessive',
                            'demonstrative',
                            'relative',
                            'interrogative',
                            'indefinite')

