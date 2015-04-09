
import logging

from copy import deepcopy
from nlg.structures import *
from nlg.microplanning import sentence_iterator


# add default logger
logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)

class ElementError(Exception):
    pass


def add_elements(e1, e2, conj='and'):
    if (not isinstance(e1, Element) or not isinstance(e2, Element)):
        raise ElementError("To add elements they have to be NLGElements")

    cc = Coordination()

    if (isinstance(e1, Coordination)):
        cc = deepcopy(e1)
        cc.coords.append(deepcopy(e2))
        if 'discourseFunction' in e2._features:
            cc._features['discourseFunction'] = e2._features['discourseFunction']

    elif (isinstance(e2, Coordination)):
        cc = deepcopy(e2)
        cc.coords.append(deepcopy(e1))
        if 'discourseFunction' in e1._features:
            cc._features['discourseFunction'] = e1._features['discourseFunction']
    else:
        cc.coords.append(deepcopy(e1))
        cc.coords.append(deepcopy(e2))
        if 'discourseFunction' in e2._features:
            cc._features['discourseFunction'] = e2._features['discourseFunction']
        elif 'discourseFunction' in e1._features:
            cc._features['discourseFunction'] = e1._features['discourseFunction']
    cc.set_feature('conj', conj)
    # TODO: figure out when it is appropriate to set number to plural
    cc.set_feature('NUMBER', 'PLURAL')
    return cc

def try_to_aggregate(sent1, sent2, marker='and'):
    """ Attempt to combine two elements into one by replacing the differing
    elements by a conjunction.

    """
    if sent1 is None or sent2 is None: return None
    if not isinstance(sent1, Clause) or not isinstance(sent2, Clause):
        return None

    replacement = Word("REPLACEMENT", "REPLACEMENT")
    for e1 in sentence_iterator(sent1):
        s1 = deepcopy(sent1)
        s1.replace(e1, replacement) # replace one element

        for e2 in sentence_iterator(sent2):
            s2 = deepcopy(sent2)
            s2.replace(e2, replacement) #replace one element

            if s1.subj is None:
                if s1.vp == replacement:
                    continue
                if (isinstance(s1.vp, Phrase) and
                    isinstance(s2.vp, Phrase) and
                    s1.vp.head != s2.vp.head):
                    continue

            # if sentences are equal (eg s1: load x; s2: load x) aggregate
            if (s1 == s2):
                get_log().debug('Aggregating:\n\t%s\n\t%s' % (str(s1), str(s2)))
                cc = add_elements(e1, e2, conj=marker)
                s1.replace(replacement, cc)
                get_log().debug('Result of aggregation:\n%s' % repr(s1))
                return s1
#            else:
#                print('Did not aggregate:\n\t%s\n\t%s' % (str(s1), str(s2)))
#                if (str(s1) == str(s2)):
#                    print('s1 == s2: %s' % str(s1 == s2))
    return None


def synt_aggregation(elements, max=3, marker='and'):
    """ Take a list of elements and combine elements that are synt. similar.

    elements - a list of elements to combine
    max      - a maximum number of elements to aggregate

    The algorithm relies on shared structure of the elements. If, for
    example, two elements share the subject, combine the VPs into
    a conjunction. Do not combine more than 'max' elements into each other.

    """
    if elements is None: return
    if len(elements) < 2: return elements
    get_log().debug('performing synt. aggr on:\n' + repr(elements))
    aggregated = list()
    i = 0
    while i < len(elements):
        msg, increment = _do_aggregate(elements, i, max, marker)
        aggregated.append(msg)
        i += increment

    return aggregated

def _do_aggregate(elements, i, max, marker='and'):
    lhs = elements[i]
    j = i + 1
    increment = 1
    while j < len(elements) and _can_aggregate(lhs, max):
        get_log().debug('LHS = %s' % lhs)
        rhs = elements[j]
        if _can_aggregate(rhs, max):
            tmp = try_to_aggregate(lhs, rhs, marker)
            if tmp is not None:
                lhs = tmp
                increment += 1
                j += 1
            else:
                break
        # cannot aggregate. can we skip it?
        elif _can_skip(elements, j):
            j += 1
            increment += 1
        else:
            break
    return (lhs, increment)

def _can_aggregate(message, max):
    """ Return true if this message can be aggregated.
    max - maximum number of coordinates in a coordingated clause
    If the message does not have a coordinated clause or if the number
    of coordinates is less then 'max', return True.

    """
    if message is None: return False
    for part in sentence_iterator(message):
        if not isinstance(part, Coordination):
            continue
        else:
            return (len(part.coords) < max)
    # simple sentence - no coordinated clause
    return True

def _can_skip(elements, j):
    """ Return true if this element can be skipped. """
    return (elements[j] is None)


def aggregate(msg, limit=5):
    """ """
    if msg is None:
        return None
    elif isinstance(msg, String):
        return msg
    elif isinstance(msg, list):
        return aggregate_list(msg)
    elif isinstance(msg, Clause):
        return aggregate_clause(msg)
    elif isinstance(msg, Coordination):
        return aggregate_coordination(msg, limit)
    elif isinstance(msg, MsgSpec):
        return msg
    elif isinstance(msg, Message):
        return aggregate_message(msg, limit)
    elif isinstance(msg, Paragraph):
        return aggregate_paragraph(msg, limit)
    elif isinstance(msg, Section):
        return aggregate_section(msg, limit)
    elif isinstance(msg, Document):
        return aggregate_document(msg, limit)
    else:
        get_log().warning('"%s" is neither a Message nor a MsgInstance' %
            str(type(msg)))
        return msg


def aggregate_list(lst):
    get_log().debug('Aggregating a list.')
    elements = []
    if len(lst) > 1:
        elements = synt_aggregation([aggregate(x) for x in lst])
    elif len(lst) == 1:
        elements.append(aggregate(lst[0]))
    return elements

def aggregate_clause(clause, marker='and'):
    """Check if clause contains a coordinated element and if so, aggregate. """
    get_log().debug('Aggregating a clause:\n' + repr(clause))
    subj = aggregate(clause.subj, 10)
    obj = aggregate(clause.complements, 10)
    vp = aggregate(clause.vp, 10)
    vp.add_features(clause.vp._features)
    c = deepcopy(clause)
    c.set_subj(subj)
    c.set_vp(vp)
    c.set_complements(*obj)
    get_log().debug('...result:\n' + repr(c))
    return c

def aggregate_coordination(cc, limit):
    get_log().debug('Aggregating coordination.')
    coords = aggregate_list(cc.coords)
    if len(coords) == 1:
        result = coords[0]
        result.add_features(cc._features)
        return result
    else:
        return Coordination(*coords, conj=cc.conj, features=cc._features)


def aggregate_message(msg, limit):
    """ Perform syntactic aggregation on the constituents.
    The aggregation is triggered only if the RST relation is
    a sequence or a list.

    """
    get_log().debug('Aggregating message.')
    if not (msg.rst == 'Sequence' or
            msg.rst == 'Alternative' or
            msg.rst == 'List'): return msg
    # TODO: Sequence and list are probably multi-nucleus and not multi-satelite
    get_log().debug('Aggregating list or sequence.')
    elements = []
    if len(msg.satelites) > 1:
        # FIXME: where does the marker go?
        if msg.marker is None or msg.marker == '':
            marker = 'and'
        else:
            marker = msg.marker
        elements = synt_aggregation(msg.satelites, limit)
    elif len(msg.satelites) == 1:
        elements.append(msg.satelites[0])
    if msg.nucleus is not None:
        elements.insert(0, msg.nucleus)
        # TODO: put elements in nucleus or come up with a different struct.
    return Message(msg.rst, None, *elements)


def aggregate_paragraph(para, limit):
    """ Perform syntactic aggregation on the constituents. """
    get_log().debug('Aggregating paragraph.')
    if para is None: return None
    messages = [aggregate(x, limit) for x in para.messages if x is not None]
    return Paragraph(*messages)


def aggregate_section(sec, limit):
    """ Perform syntactic aggregation on the constituents. """
    get_log().debug('Aggregating section.')
    if sec is None: return None
    title = aggregate(sec.title, limit)
    paragraphs = [aggregate(x, limit) for x in sec.paragraphs if x is not None]
    return Section(title, *paragraphs)


def aggregate_document(doc, limit):
    """ Perform aggregation on a document - possibly before lexicalisation. """
    get_log().debug('Aggregating document.')
    if doc is None: return None
    title = aggregate(doc.title, limit)
    sections = [aggregate(x, limit) for x in doc.sections if x is not None]
    return Document(title, *sections)



#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
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
