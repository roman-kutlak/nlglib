from copy import deepcopy
from nlg.structures import *

DEBUG = False


class ElementError(Exception):
    pass


def add_elements(e1, e2):
    if (not isinstance(e1, Element) or not isinstance(e2, Element)):
        raise ElementError("To add elements they have to be NLGElements")

    cc = CC()

    if (isinstance(e1, CC)):
        cc = deepcopy(e1)
        cc.coords.append(deepcopy(e2))
        if 'discourseFunction' in e2._features:
            cc._features['discourseFunction'] = e2._features['discourseFunction']

    elif (isinstance(e2, CC)):
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

    return cc

def try_to_aggregate(sent1, sent2):
    """ Attempt to combine two elements into one by replacing the differing 
    elements by a conjunction.
    
    """
    if sent1 is None or sent2 is None: return None
    if not isinstance(sent1, Clause) or not isinstance(sent2, Clause):
        return None

    replacement = Word("REPLACEMENT", "REPLACEMENT")
    for e1 in sentence_iterator(sent1):
        s1 = deepcopy(sent1)
        replace_element(s1, e1, replacement) # replace one element

        for e2 in sentence_iterator(sent2):
            s2 = deepcopy(sent2)
            replace_element(s2, e2, replacement) #replace one element

            if s1.subj is None:
                if s1.vp == replacement:
                    continue
                if (isinstance(s1.vp, Phrase) and
                    isinstance(s2.vp, Phrase) and
                    s1.vp.head != s2.vp.head):
                    continue
            
            # if sentences are equal (eg s1: load x; s2: load x) aggregate
            if (s1 == s2):
                if DEBUG: print ('Aggregating:\n\t%s\n\t%s' % (repr(s1), repr(s2)))
                cc = add_elements(e1, e2)
                replace_element(s1, replacement, cc)
                if DEBUG: print('Result: %s' % repr(s1))
                return s1
#            else:
#                print('Did not aggregate:\n\t%s\n\t%s' % (str(s1), str(s2)))
#                if (str(s1) == str(s2)):
#                    print('s1 == s2: %s' % str(s1 == s2))
    return None


def synt_aggregation(elements, max=3):
    """ Take a list of elements and combine elements that are synt. similar.
    
    elements - a list of elements to combine
    max      - a maximum number of elements to aggregate
    
    The algorithm relies on shared structure of the elements. If, for 
    example, two elements share the subject, combine the VPs into 
    a conjunction. Do not combine more than 'max' elements into each other.

    """
    if elements is None: return
    if len(elements) < 2: return elements

    aggregated = list()
    i = 0
    while i < len(elements) - 1:
        msg, increment = _do_aggregate(elements, i, max)
        aggregated.append(msg)
        i += increment

    return aggregated

def _do_aggregate(elements, i, max):
    lhs = elements[i]
    j = i + 1
    increment = 1
    while j < len(elements) and _can_aggregate(lhs, max):
        if DEBUG: print('LHS = %s' % lhs)
        rhs = elements[j]
        if _can_aggregate(rhs, max):
            tmp = try_to_aggregate(lhs, rhs)
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
        if not isinstance(part, CC):
            continue
        else:
            return (len(part.coords) < max)
    # simple sentence - no coordinated clause
    return True

def _can_skip(elements, j):
    """ Return true if this element can be skipped. """
    return (elements[j] is None)


def aggregate(msg, limit):
    """ """
    if msg is None:
        return None
    elif isinstance(msg, String):
        return msg
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
        raise TypeError('"%s" is neither a Message nor a MsgInstance' %
            str(type(msg)))


def aggregate_message(msg, limit):
    """ Perform syntactic aggregation on the constituents. 
    The aggregation is triggered only if the RST relation is 
    a sequence or a list.

    """
    if DEBUG: print('*** called aggregate message!')
    if not (msg.rst == 'Sequence' or msg.rst == 'List'): return msg
    # TODO: Sequence and list are probably multi-nucleus and not multi-satelite
    if DEBUG: print('*** aggregating list or sequence')
    elements = []
    if len(msg.satelites) > 1:
        elements = synt_aggregation(msg.satelites, limit)
    if msg.nucleus is not None:
        elements.insert(0, msg.nucleus)
    return Message(msg.rst, None, *elements)


def aggregate_paragraph(para, limit):
    """ Perform syntactic aggregation on the constituents. """
    if DEBUG: print('*** called aggregate paragraph!')
    if para is None: return None
    messages = [aggregate(x, limit) for x in para.messages if x is not None]
    return Paragraph(*messages)

def aggregate_section(sec, limit):
    """ Perform syntactic aggregation on the constituents. """
    if DEBUG: print('*** called aggregate section!')
    if sec is None: return None
    title = aggregate(sec.title, limit)
    paragraphs = [aggregate(x, limit) for x in sec.paragraphs if x is not None]
    return Section(title, *paragraphs)

def aggregate_document(doc, limit):
    """ Perform aggregation on a document - possibly before lexicalisation. """
    if DEBUG: print('*** called aggregate document!')
    if doc is None: return None
    title = aggregate(doc.title, limit)
    sections = [aggregate(x, limit) for x in doc.sections if x is not None]
    return Document(title, *sections)

























