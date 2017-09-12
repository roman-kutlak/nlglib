import logging

from copy import deepcopy
from nlglib.structures import *
from nlglib.microplanning import sentence_iterator

# add default logger
logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_log():
    return logging.getLogger(__name__)


class ElementError(Exception):
    pass


class AggregationError(Exception):
    pass


def add_elements(e1, e2, conj='and', **kwargs):
    if not isinstance(e1, Element) or not isinstance(e2, Element):
        raise ElementError("To add elements they have to be NLGElements")

    cc = Coordination()

    if isinstance(e1, Coordination):
        cc = deepcopy(e1)
        cc.coords.append(deepcopy(e2))
        if 'discourseFunction' in e2.features:
            cc.features['discourseFunction'] = e2.features['discourseFunction']

    elif isinstance(e2, Coordination):
        cc = deepcopy(e2)
        cc.coords.append(deepcopy(e1))
        if 'discourseFunction' in e1.features:
            cc.features['discourseFunction'] = e1.features['discourseFunction']
    else:
        cc.coords.append(deepcopy(e1))
        cc.coords.append(deepcopy(e2))
        if 'discourseFunction' in e2.features:
            cc.features['discourseFunction'] = e2.features['discourseFunction']
        elif 'discourseFunction' in e1.features:
            cc.features['discourseFunction'] = e1.features['discourseFunction']
    cc.set_feature('conj', conj)
    # TODO: figure out when it is appropriate to set number to plural
    if not cc.coords[0].has_feature('PROPER', 'true'):
        cc.set_feature('NUMBER', 'PLURAL')
    return cc


def try_to_aggregate(sent1, sent2, marker='and', **kwargs):
    """ Attempt to combine two elements into one by replacing the differing
    elements by a conjunction.

    """
    if sent1 is None or sent2 is None: return None
    if not isinstance(sent1, Clause) or not isinstance(sent2, Clause):
        return None

    replacement = Var("REPLACEMENT", "REPLACEMENT")
    for e1 in sentence_iterator(sent1):
        s1 = deepcopy(sent1)
        s1.replace(e1, replacement)  # replace one element

        for e2 in sentence_iterator(sent2):
            s2 = deepcopy(sent2)
            s2.replace(e2, replacement)  # replace one element

            if s1.subj is None:
                if s1.vp == replacement:
                    continue
                if (isinstance(s1.vp, Phrase) and
                        isinstance(s2.vp, Phrase) and
                            s1.vp.head != s2.vp.head):
                    continue

            # if sentences are equal (eg s1: load x; s2: load x) aggregate
            if s1 == s2:
                get_log().debug('Aggregating:\n\t%s\n\t%s' % (str(s1), str(s2)))
                cc = add_elements(e1, e2, conj=marker)
                s1.replace(replacement, cc)
                get_log().debug('Result of aggregation:\n%s' % repr(s1))
                return s1
           # else:
           #     print('Did not aggregate:\n\t%s\n\t%s' % (str(s1), str(s2)))
           #     if (str(s1) == str(s2)):
           #         print('s1 == s2: %s' % str(s1 == s2))
    return None


def synt_aggregation(elements, max=3, marker='and', **kwargs):
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
    aggregated = []
    # first try partial syntax aggregation  (e.g., clause + adj, etc)
    # assume format [clause, mod, mod, clause, clause, mod, clause, mod, mod...]
    new_elements = []
    i = 0
    while i < len(elements):
        e = elements[i]
        if is_clause_t(e) and i + 1 < len(elements):
            try:
                next = elements[i+1]
                while not is_clause_t(next):
                    e = e + next
                    i += 1
                    if i + 1 >= len(elements):
                        break
                    next = elements[i + 1]
            except AggregationError:
                pass
        new_elements.append(e)
        i += 1
    if len(new_elements) < 2:
        return new_elements
    i = 0
    while i < len(new_elements):
        msg, increment = _do_aggregate(new_elements, i, max, marker, **kwargs)
        if isinstance(msg, Clause):
            if msg.subj.has_feature('PROPER', 'true'):
                msg.vp.set_feature('NUMBER', 'SINGULAR')
        aggregated.append(msg)
        i += increment

    return aggregated


def _do_aggregate(elements, i, max, marker='and', **kwargs):
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
    return lhs, increment


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
            return len(part.coords) < max
    # simple sentence - no coordinated clause
    return True


def _can_skip(elements, j):
    """ Return true if this element can be skipped. """
    return elements[j] is None


def aggregate(msg, **kwargs):
    """ """
    if msg is None:
        return None
    elif isinstance(msg, String):
        return msg
    elif isinstance(msg, list):
        return aggregate_list(msg, **kwargs)
    elif isinstance(msg, Clause):
        return aggregate_clause(msg, **kwargs)
    elif isinstance(msg, Coordination):
        return aggregate_coordination(msg, **kwargs)
    elif isinstance(msg, MsgSpec):
        return msg
    elif isinstance(msg, Message):
        return aggregate_message(msg, **kwargs)
    # elif isinstance(msg, Paragraph):
    #     return aggregate_paragraph(msg, **kwargs)
    # elif isinstance(msg, Section):
    #     return aggregate_section(msg, **kwargs)
    elif isinstance(msg, Document):
        return aggregate_document(msg, **kwargs)
    else:
        #        get_log().warning('"%s" is neither a Message nor a MsgInstance' %
        #            str(type(msg)))
        return deepcopy(msg)


def aggregate_list(lst, **kwargs):
    get_log().debug('Aggregating a list.')
    elements = []
    if len(lst) > 1:
        elements = synt_aggregation([aggregate(x, **kwargs) for x in lst])
    elif len(lst) == 1:
        elements.append(aggregate(lst[0]))
    return elements


def aggregate_clause(clause, **kwargs):
    """Check if clause contains a coordinated element and if so, aggregate. """
    get_log().debug('Aggregating a clause:\n' + repr(clause))
    subj = aggregate(clause.subj, **kwargs)
    complements = aggregate(clause.complements, **kwargs)
    vp = aggregate(clause.vp, **kwargs)
    vp.features.update(clause.vp.features)
    c = deepcopy(clause)
    c.subject = subj
    c.predicate = vp
    c.complements = complements
    get_log().debug('...result:\n' + repr(c))
    return c


def aggregate_coordination(cc, **kwargs):
    get_log().debug('Aggregating coordination.')
    coords = aggregate_list(cc.coords, **kwargs)
    if len(coords) == 1:
        result = coords[0]
        result.features.update(cc.features)
        return result
    else:
        return Coordination(*coords, conj=cc.conj, features=cc.features)


def aggregate_message(msg, **kwargs):
    """ Perform syntactic aggregation on the constituents.
    The aggregation is triggered only if the RST relation is
    a sequence or a list.

    """
    get_log().debug('Aggregating message.')
    relation = msg.relation.lower()
    if relation not in ('sequence', 'alternative', 'list'):
        return msg
    # TODO: Sequence and list are probably multi-nuclei and not multi-satellite
    get_log().debug('Aggregating list or sequence.')
    elements = []
    if msg.is_multinuclear:
        # FIXME: where does the marker go?
        if msg.marker is None or msg.marker == '':
            marker = 'and'
        else:
            marker = msg.marker
        elements = synt_aggregation([aggregate(s, **kwargs) for s in msg.nuclei],
                                    **kwargs)
    else:
        elements.append(msg.nucleus)
    if msg.satellite is not None:
        elements.append(msg.satellite)
        # TODO: put elements in nuclei or come up with a different struct.
    return Message(relation, *elements)


# def aggregate_paragraph(para, **kwargs):
#     """ Perform syntactic aggregation on the constituents. """
#     get_log().debug('Aggregating paragraph.')
#     if para is None: return None
#     messages = [aggregate(x, **kwargs) for x in para.messages if x is not None]
#     return Paragraph(*messages)
#
#
# def aggregate_section(sec, **kwargs):
#     """ Perform syntactic aggregation on the constituents. """
#     get_log().debug('Aggregating section.')
#     if sec is None: return None
#     title = aggregate(sec.title, **kwargs)
#     paragraphs = [aggregate(x, **kwargs) for x in sec.content if x is not None]
#     return Section(title, *paragraphs)


def aggregate_document(doc, **kwargs):
    """ Perform aggregation on a document - possibly before lexicalisation. """
    get_log().debug('Aggregating document.')
    if doc is None: return None
    title = aggregate(doc.title, **kwargs)
    sections = [aggregate(x, **kwargs) for x in doc.sections if x is not None]
    return Document(title, *sections)
