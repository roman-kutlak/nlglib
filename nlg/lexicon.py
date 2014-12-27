from nlg.structures import Word

""" This module serves as a simple lexicon. It allows the user to create
word elements of the appropriate category easily. """


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
