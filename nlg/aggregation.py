from copy import deepcopy
from nlg.structures import *


def s_aggr(sent1, sent2):
    """ Subject aggregation
        E.g. John is a boy + John is tall => John is a boy and is tall.

    """
    if sent1.subj == sent2.subj:
        coord_pred = CC([deepcopy(sent1.vp), deepcopy(sent2.vp)])
        clause = deepcopy(sent1)
        clause.vp = coord_pred
        return clause
    else:
        return None


def sp_aggr(sent1, sent2):
    """ Subject and Predicate aggregation

        E.g. John is a boy + John is tall => John is a boy and tall.

    """
    return None


def p_aggr(sent1, sent2):
    """ Predicate aggregation
        E.g. John has a pen + Mary has a book => 
            John and Mary have a book and a pen.
        "have" is a predicate aggregation
        
    """
    return None


def pdo_aggr(sent1, sent2):
    """ Predicate and Direct Object aggregation
        E.g. John wrote an article + Mary wrote an article =>
            John and Mary wrote an article
        
    """
    if sent1.vp == sent2.vp:
        coord_subject = CC([deepcopy(sent1.subj),
                                           deepcopy(sent2.subj)])
        clause = deepcopy(sent1)
        clause.subj = coord_subject
        clause.vp.features["number"] = "PLURAL";
        return clause
    else:
        return None


def do_aggr(sent1, sent2):
    """ Direct Object aggregation
        E.g. Put the apple in the basket + Put the pear in the basket =>
             Put the apple and the pear in the basket.
        
    """
    if sent1 == sent2:
        return sent1
    
    if (sent1.subj != sent2.subj or
        sent1.vp.head != sent2.vp.head):
        return None

    s1 = deepcopy(sent1)
    s2 = deepcopy(sent2)
    o1 = s1.vp.get_object()
    o2 = s2.vp.get_object()
    if (o1 is not None and o2 is not None):
        s1.vp.set_object(None)
        s2.vp.set_object(None)
        new_sent = s1
        try:
            if (s1.vp == s2.vp):
                # the vps are same (except for objects)
                del o1.features['discourseFunction']
                del o2.features['discourseFunction']
                coord_obj = CC([o1, o2])
                new_sent.vp.set_object(coord_obj)
        except Exception as e:
            print("Exception: %s" % e)
            return None

        return new_sent

    return None


def sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.vp):
            yield x
        yield sent.vp
        yield sent.subj
    
        return
    
    if isinstance(sent, Phrase):
        for o in reversed(sent.post_modifier):
            for x in sentence_iterator(o):
                yield x

        for o in reversed(sent.complement):
            for x in sentence_iterator(o):
                yield x

        if sent.head is not None:
            for x in sentence_iterator(sent.head):
                yield x

        for o in reversed(sent.pre_modifier):
            for x in sentence_iterator(o):
                yield x

        if isinstance(sent, NP):
            for x in sentence_iterator(sent.spec):
                yield x

        for o in reversed(sent.front_modifier):
            for x in sentence_iterator(o):
                yield x

    if isinstance(sent, CC):
        for x in sent.coords:
            yield x
        yield sent

    else:
        yield (sent)


def aggregation_sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.vp):
            yield x
        return

    if isinstance(sent, Phrase):
        for o in reversed(sent.post_modifier):
            for x in sentence_iterator(o):
                yield x

    for o in reversed(sent.complement):
        for x in sentence_iterator(o):
            yield x

    for o in reversed(sent.pre_modifier):
        for x in sentence_iterator(o):
            yield x

    else:
        yield (sent)


def replace_element(sent, elt, replacement=None):
    if sent == elt:
        return True
    
    if isinstance(sent, Clause):
        if sent.subj == elt:
            sent.subj = replacement
            return True
        else:
            if replace_element(sent.subj, elt, replacement):
                return True;

        if sent.vp == elt:
            sent.vp = replacement
            return True

        else:
            if replace_element(sent.vp, elt, replacement):
                return True;

    if isinstance(sent, CC):
        for i, o in list(enumerate(sent.coords)):
            if (o == elt):
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True

    if isinstance(sent, Phrase):
        res = False
        for i, o in reversed(list(enumerate(sent.post_modifier))):
            if (o == elt):
                if replacement is None:
                    del sent.post_modifier[i]
                else:
                    sent.post_modifier[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

        for i, o in reversed(list(enumerate(sent.complement))):
            if (o == elt):
                if replacement is None:
                    del sent.complement[i]
                else:
                    sent.complement[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

        if sent.head == elt:
            sent.head = replacement
            return True

        for i, o in reversed(list(enumerate(sent.pre_modifier))):
            if (o == elt):
                if replacement is None:
                    del sent.pre_modifier[i]
                else:
                    sent.pre_modifier[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

        if isinstance(sent, NP):
            if sent.spec == elt:
                sent.spec = replacement
                return True

        for i, o in reversed(list(enumerate(sent.front_modifier))):
            if (o == elt):
                if replacement is None:
                    del sent.front_modifier[i]
                else:
                    sent.front_modifier[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

    return False


# the above should be all deprecated

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
                print ('Aggregating:\n\t%s\n\t%s' % (repr(s1), repr(s2)))
                cc = add_elements(e1, e2)
                replace_element(s1, replacement, cc)
                print('Result: %s' % repr(s1))
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
        print('LHS = %s' % lhs)
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
    print('*** called aggregate message!')
    if not (msg.rst == 'Sequence' or msg.rst == 'List'): return msg
    # TODO: Sequence and list are probably multi-nucleus and not multi-satelite
    print('*** aggregating list or sequence')
    elements = []
    if len(msg.satelites) > 1:
        elements = synt_aggregation(msg.satelites, limit)
    if msg.nucleus is not None:
        elements.insert(0, self.nucleus)
    return Message(msg.rst, None, *elements)


def aggregate_paragraph(para, limit):
    """ Perform syntactic aggregation on the constituents. """
    print('*** called aggregate paragraph!')
    if para is None: return None
    messages = [aggregate(x, limit) for x in para.messages if x is not None]
    return Paragraph(*messages)

def aggregate_section(sec, limit):
    """ Perform syntactic aggregation on the constituents. """
    print('*** called aggregate section!')
    if sec is None: return None
    title = aggregate(sec.title, limit)
    paragraphs = [aggregate(x, limit) for x in sec.paragraphs if x is not None]
    return Section(title, *paragraphs)

def aggregate_document(doc, limit):
    """ Perform aggregation on a document - possibly before lexicalisation. """
    print('*** called aggregate document!')
    if doc is None: return None
    title = aggregate(doc.title, limit)
    sections = [aggregate(x, limit) for x in doc.sections if x is not None]
    return Document(title, *sections)

























