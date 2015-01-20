import logging
from collections import defaultdict
from copy import deepcopy
from pickle import load
import xml.etree.ElementTree as ET

from nlg.structures import Word

def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())

""" This module serves as a simple lexicon. It allows the user to create
word elements of the appropriate category easily. 

"""


POS_ANY = 'ANY'
POS_ADJECTIVE = 'ADJECTIVE'
POS_ADVERB = 'ADVERB'
POS_AUXILIARY = 'AUXILIARY'
POS_COMPLEMENTISER = 'COMPLEMENTISER'
POS_CONJUNCTION = 'CONJUNCTION'
POS_DETERMINER = 'DETERMINER'
POS_MODAL = 'MODAL'
POS_NOUN = 'NOUN'
POS_NUMERAL = 'NUMERAL'
POS_PREPOSITION = 'PREPOSITION'
POS_PRONOUN = 'PRONOUN'
POS_SYMBOL = 'SYMBOL'
POS_VERB = 'VERB'

# tags without POS_ANY
POS_TAGS = [
    POS_ADJECTIVE,
    POS_ADVERB,
    POS_AUXILIARY,
    POS_COMPLEMENTISER,
    POS_CONJUNCTION,
    POS_DETERMINER,
    POS_MODAL,
    POS_NOUN,
    POS_NUMERAL,
    POS_PREPOSITION,
    POS_PRONOUN,
    POS_SYMBOL,
    POS_VERB
]


class Lexicon:
    """ A class that represents a lexicon. """

    def __init__(self):
        # dict of all words ([id] -> Word())
        self._words = dict()
        # mapping from word IDs to Word elements (with tags from NIH lexicon)
        self._verb = dict()
        self._aux = dict()
        self._modal = dict()
        self._noun = dict()
        self._pron = dict()
        self._adj = dict()
        self._adv = dict()
        self._prep = dict()
        self._conj = dict()
        self._compl = dict()
        self._det = dict()
        self._num = dict()
        self._sym = dict()
        # mapping from lexems (including base) to corresponding ids
        self._variants = defaultdict(set)
        # setup tagger if supported:
        try:
            with open('nlg/resources/tagger.pkl', 'rb') as input:
                self.tagger = load(input)
        except Exception as e:
            get_log().exception('Could not load pickled tagger.')
            self.tagger = None
    
    def word(self, string, pos=POS_ANY, default=None):
        """ Return a word element corresponding to the given POS or None. 
        When default is set to the string 'new' the method returns
        a new element with the given tag when no corresponding word
        exists in the lexicon.
        
        When pos is set to POS_ANY, the method picks the most likely POS tag
        for the given word.
        
        # assuming foo is not in lexicon
        >>> w = lexicon.word('foo', POS_NOUN)
        None
        >>> w = lexicon.word('foo', POS_NOUN, 'new')
        Word('foo', 'NOUN')
        >>> w = lexicon.word('foo')
        Word('foo', X) # X determined by tagger
        
        """
        if POS_ANY == pos:
            ids = list(self._variants[string])
            if len(ids) == 0: return Word(string, POS_ANY)
            elif len(ids) == 1:
                w = deepcopy(self._words[ids[0]])
                w.word = string
                fs = self.features_for_variant(w, string)
                for k, v in fs: w.set_feature(k, v)
                return w
            # otherwise try the different word categories
            else:
                return self.autotagged_word(string)
        elif pos in POS_TAGS:
            map = self._get_wordmap_for_tag(pos)
            ids = self._variants[string]
            for id in ids:
                if id in map:
                    w = deepcopy(map[id])
                    w.word = string
                    fs = self.features_for_variant(string)
                    for k, v in fs: w.set_feature(k, v)
                    return w
            # if we didn't find anything, return the default
            if 'new' == default: return Word(string, pos)
            else:                return default
        else:
            # an unknown tag passed -- try to find the correct one
            raise Exception('Unknown tag')

    def adjective(self, string):
        """ Return a word as an adjective. """
        return self.word(string, POS_ADJECTIVE, 'new')

    def adverb(self, string):
        """ Return a word as an adverb. """
        return self.word(string, POS_ADVERB, 'new')
    
    def auxiliary(self, string):
        """ Return a word as an auxiliary. """
        return self.word(string, POS_AUXILIARY, 'new')

    def complementiser(self, string):
        """ Return a word as a complementiser. """
        return self.word(string, POS_COMPLEMENTISER, 'new')

    def conjunction(self, string):
        """ Return a word as a conjunction. """
        return self.word(string, POS_CONJUNCTION, 'new')

    def determiner(self, string):
        """ Return a word as a determiner. """
        return self.word(string, POS_DETERMINER, 'new')

    def modal(self, string):
        """ Return a word as a modal. """
        return self.word(string, POS_MODAL, 'new')

    def noun(self, string):
        """ Return a word as a noun. """
        return self.word(string, POS_NOUN, 'new')

    def numeral(self, string):
        """ Return a word as a numeral. """
        return self.word(string, POS_NUMERAL, 'new')

    def preposition(self, string):
        """ Return a word as a preposition. """
        return self.word(string, POS_PREPOSITION, 'new')

    def pronoun(self, string):
        """ Return a word as a pronoun. """
        return self.word(string, POS_PRONOUN, 'new')

    def symbol(self, string):
        """ Return a word as a symbol. """
        return self.word(string, POS_SYMBOL, 'new')

    def verb(self, string):
        """ Return a word as a verb. """
        return self.word(string, POS_VERB, 'new')

    def pos_tags_for(self, string):
        """ Return a list of possible POS tags for this string. """
        ids = self._variants[string]
        tags = set()
        for id in ids:
            if   id in self._verb: tags.add(POS_VERB)
            elif id in self._aux: tags.add(POS_VERB)
            elif id in self._modal: tags.add(POS_VERB)
            elif id in self._noun: tags.add(POS_NOUN)
            elif id in self._pron: tags.add(POS_PRONOUN)
            elif id in self._adj: tags.add(POS_ADJECTIVE)
            elif id in self._adv: tags.add(POS_ADVERB)
            elif id in self._prep: tags.add(POS_PREPOSITION)
            elif id in self._conj: tags.add(POS_CONJUNCTION)
            elif id in self._compl: tags.add(POS_COMPLEMENTISER)
            elif id in self._det: tags.add(POS_DETERMINER)
            elif id in self._num: tags.add(POS_NUMERAL)
            elif id in self._sym: tags.add(POS_SYMBOL)
        return tags

    def features_for_variant(self, word, variant):
        """ Find the most likely features for the given variant. """
        # FIXME: implement
        return {}
    
    def autotagged_word(self, word):
        """ Find the most likely tag for the given word. 
        This method will try to uses NLTK tagger if NLTK is available.
        Otherwise it will search for the given word in this order:
        nouns, verbs, adjectives, adverbs, pronouns, prepositions, conjunctions,
        complementisers, numeral, symbol. If the word is not in the lexicon,
        it is tagged as a POS_SYMBOL.
        
        """
        if self.tagger is not None:
            w, tag = self.tagger.tag([word])
            # map corpus tags to our tags
            fs = self.brown_tag_to_features(tag)
            t = self.brown_tag_to_standard_tag(tag)
            candidate = self.word(w, t, 'new')
            for k, v in fs: candidate.set_feature(k, v)
            return candidate
        else:
            return (self.noun(word) or self.verb(word) or self(auxiliary) or
                    self.modal(word) or self.adjective(word) or
                    self.adverb(word) or self.pronoun(word) or
                    self.preposition(word) or self.conjunction(word) or
                    self.complementiser(word) or self.numeral(word) or
                    self.symbol(word, 'new'))

    def brown_tag_to_features(self, tag):
        """ Return the features corresponding to the given (Brown corp) tag. """
        features = {}
        if tag.endswith('$'):
            features['POSSESSIVE'] = 'TRUE'
            if not tag.startswith('PrepositionalPhrase'):
                features['CASE'] = 'GENITIVE'
        if tag.endswith('*'): features['NEGATION'] = 'TRUE'
        if tag.startswith('NounPhrase'): features['PROPER'] = 'TRUE'
        if tag.startswith('NNS'): features['NUMBER'] = 'PLURAL'
        if tag.startswith('NPS'): features['NUMBER'] = 'PLURAL'
        if tag.startswith('JJR'): features['COMPARATIVE'] = 'TRUE'
        if tag.startswith('JJS'): features['SUPERLATIVE'] = 'TRUE'
        if tag.startswith('JJT'): features['SUPERLATIVE'] = 'TRUE'
        if tag.startswith('VB'): features['BASE_FORM'] = 'TRUE'
        if tag.startswith('VBD'): features['TENSE'] = 'PAST'
        if tag.startswith('VBG'): features['TENSE'] = 'PRESENT_PARTICIPLE'
        if tag.startswith('VBN'): features['TENSE'] = 'PAST_PARTICIPLE'
        if tag.startswith('VBP'): features['TENSE'] = 'PRESENT'
        if tag.startswith('VBZ'): features['TENSE'] = 'PRESENT3S'
        # TODO: implement the rest of the table...
        #   http://www.scs.leeds.ac.uk/ccalas/tagsets/brown.html
        return features

    def brown_tag_to_standard_tag(self, tag):
        """ Map a Brown corpus tag to one of the POS_TAGS.
        If the tag is not in the lookup table, return POS_SYMBOL.
        The function simplifies most combinations of tags eg.
        MD+HV = modal auxillary + verb "to have" as in "shouldda" -> POS_MODAL.
        
        """
        if tag.startswith('A'): return POS_DETERMINER
        if tag.startswith('B'): return POS_VERB # be, is, was, isn't, ...
        if tag == 'Coordination' or tag == 'CS': return POS_CONJUNCTION
        if tag.startswith('CD'): return POS_NUMERAL
        if tag.startswith('DO'): return POS_VERB # do, did, didn't, ...
        if tag.startswith('DT'): return POS_DETERMINER
        if tag.startswith('EX'): return POS_ADVERB # existential 'there'
        # ignore foreign words -- use the attached tag (FW-JJ -> JJ)
        if tag.startswith('FW-'): return self.brown_tag_to_standard_tag(tag[3:])
        if tag.startswith('HV'): return POS_VERB # has, had, didn't have, ...
        if tag.startswith('IN'): return POS_PREPOSITION
        if tag.startswith('J'): return POS_ADJECTIVE
        if tag.startswith('MD'): return POS_MODAL
        if tag.startswith('N'): return POS_NOUN
        if tag.startswith('OD'): return POS_NUMERAL
        if tag.startswith('PN'): return POS_PRONOUN
        if tag.startswith('PrepositionalPhrase'): return POS_PRONOUN
        if tag.startswith('Q'): return POS_DETERMINER
        if tag.startswith('R'): return POS_ADVERB
        if tag.startswith('TO'): return POS_VERB
        if tag.startswith('V'): return POS_VERB
        if tag.startswith('WDT'): return POS_DETERMINER
        if tag.startswith('WP'): return POS_PRONOUN
        if tag.startswith('WQ'): return POS_ADVERB
        if tag.startswith('WR'): return POS_ADVERB
        # unknown tag?
        return POS_SYMBOL

    @property
    def words(self):
        """ Return an iterator to all words in the lexicon. """
        return self._words.values()

    def insert_word(self, word):
        """ Insert a word into the lexicon.
        The word should have base, id and pos. 
        
        """
        assert (word.base is not None and word.base != '')
        assert (word.pos is not None and word.pos != '')
        assert (word.id is not None and word.id != '')
        map = self._get_wordmap_for_tag(word.pos)
        if map is None: raise Exception('Unknown POS tag "{0}" for word "{1}"'\
                                        .format(word.pos, word.word))
        map[word.id] = word
        self._words[word.id] = word
        self._variants[word.base].add(word.id)
    
    def insert_variant(self, word, variant):
        """ Insert a variant of an existing word element. """
        self._variants[variant].add(word.id)

    def _get_wordmap_for_tag(self, pos):
        if   POS_VERB == pos: return self._verb
        elif POS_NOUN == pos: return self._noun
        elif POS_PRONOUN == pos: return self._pron
        elif POS_ADJECTIVE == pos: return self._adj
        elif POS_ADVERB == pos: return self._adv
        elif POS_PREPOSITION == pos: return self._prep
        elif POS_CONJUNCTION == pos: return self._conj
        elif POS_COMPLEMENTISER == pos: return self._compl
        elif POS_DETERMINER == pos: return self._det
        elif POS_NUMERAL == pos: return self._num
        elif POS_SYMBOL == pos: return self._sym
        else: return None

    def template_for_noun(self, word):
        """ Assuming word is an instance of Word() that can be used as a noun,
        create a template with this word.
        
        """
        pass


def lexicon_from_nih_xml(path):
    """ Create a new instance of a Lexicon from the NIH lexicon in XML. """
    nih_tag_map = {
        '' : POS_ANY, # not in NIH
        'adj' : POS_ADJECTIVE,
        'adv' : POS_ADVERB,
        'aux' : POS_AUXILIARY,
        'compl' : POS_COMPLEMENTISER,
        'conj' : POS_CONJUNCTION,
        'det' : POS_DETERMINER,
        'modal' : POS_MODAL,
        'noun' : POS_NOUN,
        'num' : POS_NUMERAL,
        'prep' : POS_PREPOSITION,
        'pron' : POS_PRONOUN,
        'sym' : POS_SYMBOL, # not in NIH
        'verb' : POS_VERB,
    }
    lexicon = Lexicon()
    tree = ET.parse(path)
    lexrecords = tree.getroot()
    for lexrecord in lexrecords:
        w = Word('', '')
        tag = lexrecord.find('base')
        if tag is not None:
            w.word = tag.text
            w.base = tag.text
        tag = lexrecord.find('eui')
        if tag is not None:
            w.id = tag.text
        tag = lexrecord.find('cat')
        if tag is not None:
            w.pos = nih_tag_map[tag.text]
        lexicon.insert_word(w)
        for variant in lexrecord.iter('inflVars'):
            lexicon.insert_variant(w, variant.text)
    return lexicon


# nouns with irregular plural form
irregulars = {
    'addendum': 'addenda',
    'aircraft': 'aircraft',
    'alumna': 'alumnae',
    'alumnus': 'alumni',
    'analysis': 'analyses',
    'antenna': 'antennae',
    'antithesis': 'antitheses',
    'apex': 'apices',
    'appendix': 'appendices',
    'avocado': 'avocados',
    'axis': 'axes',
    'bacillus': 'bacilli',
    'bacterium': 'bacteria',
    'basis': 'bases',
    'beau': 'beaux',
    'bison': 'bison',
    'bureau': 'bureaux',
    'cactus': 'cacti',
    'château': 'châteaux',
    'child': 'children',
    'chief': 'chiefs',
    'codex': 'codices',
    'concerto': 'concerti',
    'corpus': 'corpora',
    'crisis': 'crises',
    'criterion': 'criteria',
    'curriculum': 'curricula',
    'datum': 'data',
    'deer': 'deer',
    'diagnosis': 'diagnoses',
    'die': 'dice',
    'dwarf': 'dwarves',
    'ellipsis': 'ellipses',
    'embryo': 'embryos',
    'epoch': 'epochs',
    'erratum': 'errata',
    'faux pas': 'faux pas',
    'fez': 'fezzes',
    'fish': 'fish',
    'focus': 'foci',
    'foot': 'feet',
    'formula': 'formulae',
    'fungus': 'fungi',
    'genus': 'genera',
    'goose': 'geese',
    'graffito': 'graffiti',
    'grouse': 'grouse',
    'half': 'halves',
    'hoof': 'hooves',
    'hypothesis': 'hypotheses',
    'index': 'indices',
    'larva': 'larvae',
    'libretto': 'libretti',
    'loaf': 'loaves',
    'locus': 'loci',
    'louse': 'lice',
    'man': 'men',
    'matrix': 'matrices',
    'medium': 'media',
    'memorandum': 'memoranda',
    'minutia': 'minutiae',
    'monarch': 'monarchs',
    'moose': 'moose',
    'mouse': 'mice',
    'nebula': 'nebulae',
    'nucleus': 'nuclei',
    'oasis': 'oases',
    'offspring': 'offspring',
    'opus': 'opera',
    'ovum': 'ova',
    'ox': 'oxen',
    'parenthesis': 'parentheses',
    'person': 'people',
    'phenomenon': 'phenomena',
    'phylum': 'phyla',
    'prognosis': 'prognoses',
    'quiz': 'quizzes',
    'radius': 'radii',
    'referendum': 'referenda',
    'salmon': 'salmon',
    'scarf': 'scarves',
    'self': 'selves',
    'series': 'series',
    'sheep': 'sheep',
    'shrimp': 'shrimp',
    'species': 'species',
    'solo': 'solos',
    'spoof': 'spoofs',
    'stimulus': 'stimuli',
    'stomach': 'stomachs',
    'stratum': 'strata',
    'swine': 'swine',
    'syllabus': 'syllabi',
    'symposium': 'symposia',
    'synopsis': 'synopses',
    'tableau': 'tableaux',
    'thesis': 'theses',
    'thief': 'thieves',
    'tooth': 'teeth',
    'trout': 'trout',
    'tuna': 'tuna',
    'vertebra': 'vertebrae',
    'vertex': 'vertices',
    'vita': 'vitae',
    'vortex': 'vortices',
    'wharf': 'wharves',
    'wife': 'wives',
    'wolf': 'wolves',
    'woman': 'women',
    'zero': 'zeros',
}


def is_vowel(l):
    return l in {'a', 'e', 'i', 'o', 'u'}


# a helper function used for simple realisation when lexicon is not available
def pluralise_noun(word):
    if word in irregulars: return irregulars[word]
    if word == '': return ''
    if len(word) == 1: return word + 's'
    if word[-2:] in {'ch', 'sh', 'ss'}: return word + 'es'
    if word[-1:] in {'s', 'x', 'z'}: return word + 'es'
    if word[-1]  == 'y' and not is_vowel(word[-2]): return word[:-1] + 'ies'
    if word[-1]  == 'f': return word[:-1] + 'ves'
    if word[-2:] == 'fe': return word[:-2] + 'ves'
    if word[-1]  == 'o' and not is_vowel(word[-2]): return word + 'es'
    return word + 's'


#############################################################################
##
## Copyright (C) 2014 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################
